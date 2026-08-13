from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.insight_repository import InsightRepository
from app.repositories.recommendation_repository import RecommendationRepository, evidence_json
from app.services.analytics_service import analytics_service


class RecommendationService:
    """Rule-based healthcare-finance recommendations; no clinical decisions or savings claims."""

    def __init__(self) -> None:
        self.insights = InsightRepository()
        self.recommendations = RecommendationRepository()

    def generate(self, db: Session, dataset_id: int):
        summary = analytics_service.get_summary(db, dataset_id)
        alerts = self.insights.list_alerts(db, dataset_id)
        drivers = self.insights.list_drivers(db, dataset_id)
        settings = get_settings()
        items: list[dict[str, object]] = []
        alert_by_metric = {alert.metric: alert for alert in alerts}
        driver_by_metric = {driver.metric: driver for driver in drivers}

        concentration = alert_by_metric.get("Department cost concentration")
        if concentration:
            items.append(_item(
                title="Review high-cost department economics",
                category="Department cost management",
                priority=concentration.severity,
                rationale="Investigate department utilization, pricing, and service mix before the concentration becomes a larger budget exposure.",
                evidence=[concentration.explanation, _forecast_context(db, dataset_id)],
                triggering_metric=concentration.metric,
                period=concentration.period,
            ))

        utilization = driver_by_metric.get("Patient utilization")
        if utilization and (utilization.change_pct or 0) >= settings.alert_mom_cost_threshold_pct:
            items.append(_item(
                title="Review utilization and site-of-care patterns",
                category="Utilization management",
                priority="medium",
                rationale="Assess operational utilization patterns and site-of-care mix for opportunities to manage avoidable cost pressure.",
                evidence=[utilization.explanation, _forecast_context(db, dataset_id)],
                triggering_metric=utilization.metric,
                period=utilization.period,
            ))

        cost_per_patient = driver_by_metric.get("Cost per patient")
        if cost_per_patient and (cost_per_patient.change_pct or 0) >= settings.alert_cost_per_patient_threshold_pct:
            items.append(_item(
                title="Review unit cost and service mix",
                category="Unit cost management",
                priority="medium",
                rationale="Review operational unit-cost and service-mix factors behind the observed growth in cost per patient.",
                evidence=[cost_per_patient.explanation, _forecast_context(db, dataset_id)],
                triggering_metric=cost_per_patient.metric,
                period=cost_per_patient.period,
            ))
        return self.recommendations.replace(db, dataset_id, items)

    def list(self, db: Session, dataset_id: int):
        analytics_service.get_summary(db, dataset_id)
        return self.recommendations.list(db, dataset_id)


def _item(*, title: str, category: str, priority: str, rationale: str, evidence: list[str], triggering_metric: str, period: str) -> dict[str, object]:
    return {"title": title, "category": category, "priority": priority, "rationale": rationale, "supporting_evidence": evidence_json([item for item in evidence if item]), "triggering_metric": triggering_metric, "period": period}


def _forecast_context(db: Session, dataset_id: int) -> str:
    from app.db.models.forecast_run import ForecastRun
    from sqlalchemy import select
    run = db.scalar(select(ForecastRun).where(ForecastRun.dataset_id == dataset_id).order_by(ForecastRun.created_at.desc()))
    return f"Latest existing forecast uses {run.model_name} for a {run.horizon_months}-month horizon." if run else ""


recommendation_service = RecommendationService()
