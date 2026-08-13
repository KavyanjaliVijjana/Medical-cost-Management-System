from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.insight_repository import InsightRepository
from app.services.analytics_service import analytics_service


class AlertService:
    """Configurable deterministic cost-pressure rules with traceable thresholds."""

    def __init__(self) -> None:
        self.repository = InsightRepository()

    def generate(self, db: Session, dataset_id: int):
        summary = analytics_service.get_summary(db, dataset_id)
        settings = get_settings()
        items: list[dict[str, object]] = []
        trend = summary.monthly_trend
        if len(trend) >= 2:
            current, previous = trend[-1], trend[-2]
            if current.month_over_month_cost_change_pct is not None and current.month_over_month_cost_change_pct >= settings.alert_mom_cost_threshold_pct:
                items.append(_alert("Month-over-month total cost increase", current.month_over_month_cost_change_pct, settings.alert_mom_cost_threshold_pct, current.month, f"Total cost rose {current.month_over_month_cost_change_pct:.1f}% from {previous.month} to {current.month}."))
            if current.cost_per_patient is not None and previous.cost_per_patient not in (None, 0):
                change = round(((current.cost_per_patient - previous.cost_per_patient) / previous.cost_per_patient * 100), 2)
                if change >= settings.alert_cost_per_patient_threshold_pct:
                    items.append(_alert("Cost-per-patient increase", change, settings.alert_cost_per_patient_threshold_pct, current.month, f"Cost per patient rose {change:.1f}% from {previous.month} to {current.month}."))
        if summary.highest_cost_department is not None and (summary.highest_cost_department.contribution_pct or 0) >= settings.alert_department_concentration_threshold_pct:
            department = summary.highest_cost_department
            items.append(_alert("Department cost concentration", department.contribution_pct or 0, settings.alert_department_concentration_threshold_pct, "Historical dataset", f"{department.department} represents {department.contribution_pct or 0:.1f}% of total medical cost."))
        return self.repository.replace_alerts(db, dataset_id, items)

    def list(self, db: Session, dataset_id: int):
        analytics_service.get_summary(db, dataset_id)
        return self.repository.list_alerts(db, dataset_id)


def _alert(metric: str, observed: float, threshold: float, period: str, explanation: str) -> dict[str, object]:
    return {"severity": "high" if observed >= threshold * 2 else "medium", "metric": metric, "observed_value": observed, "threshold_value": threshold, "period": period, "explanation": explanation, "status": "active"}


alert_service = AlertService()
