from sqlalchemy.orm import Session

from app.repositories.insight_repository import InsightRepository
from app.services.analytics_service import analytics_service


class DriverAnalysisService:
    """Transparent descriptive driver signals computed from existing historical analytics."""

    def __init__(self) -> None:
        self.repository = InsightRepository()

    def generate(self, db: Session, dataset_id: int):
        summary = analytics_service.get_summary(db, dataset_id)
        trend = summary.monthly_trend
        items: list[dict[str, object]] = []
        if len(trend) >= 2:
            current, previous = trend[-1], trend[-2]
            items.extend([
                _change_item("Month-over-month total cost", current.total_cost, previous.total_cost, current.month, "Total medical cost"),
                _change_item("Patient utilization", float(current.patient_count), float(previous.patient_count), current.month, "Patient volume"),
            ])
            if current.cost_per_patient is not None and previous.cost_per_patient is not None:
                items.append(_change_item("Cost per patient", current.cost_per_patient, previous.cost_per_patient, current.month, "Cost per patient"))
        if summary.highest_cost_department is not None:
            department = summary.highest_cost_department
            items.append({
                "metric": "Department cost contribution",
                "observed_value": department.total_cost,
                "baseline_value": summary.metrics.total_medical_cost,
                "change_pct": department.contribution_pct,
                "period": "Historical dataset",
                "explanation": f"{department.department} accounts for {department.contribution_pct or 0:.1f}% of total medical cost.",
            })
        return self.repository.replace_drivers(db, dataset_id, items)

    def list(self, db: Session, dataset_id: int):
        analytics_service.get_summary(db, dataset_id)
        return self.repository.list_drivers(db, dataset_id)


def _change_item(metric: str, observed: float, baseline: float, period: str, label: str) -> dict[str, object]:
    change = round(((observed - baseline) / baseline) * 100, 2) if baseline else None
    direction = "increased" if change is not None and change >= 0 else "decreased"
    return {
        "metric": metric,
        "observed_value": observed,
        "baseline_value": baseline,
        "change_pct": change,
        "period": period,
        "explanation": f"{label} {direction} by {abs(change or 0):.1f}% compared with the prior month.",
    }


driver_analysis_service = DriverAnalysisService()
