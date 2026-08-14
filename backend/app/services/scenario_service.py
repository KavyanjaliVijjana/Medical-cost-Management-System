from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.forecast_repository import ForecastRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.services.analytics_service import analytics_service


class ScenarioService:
    """Deterministic cost-share what-if calculations; it does not estimate causal savings."""

    def __init__(self) -> None:
        self.forecasts = ForecastRepository()
        self.scenarios = ScenarioRepository()

    def create(self, db: Session, *, dataset_id: int, department: str, reduction_pct: float):
        summary = analytics_service.get_summary(db, dataset_id)
        forecast_run = self.forecasts.get_latest_for_dataset(db, dataset_id)
        if forecast_run is None or not forecast_run.points:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A persisted forecast with forecast points is required before calculating a scenario.",
            )

        selected_department = next(
            (item for item in summary.departments if item.department == department), None
        )
        if selected_department is None or selected_department.contribution_pct is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected department is not present in the dataset or has no cost share.",
            )

        calculation = self.calculate(
            baseline_projected_cost=sum(point.predicted_cost for point in forecast_run.points),
            department_cost_share_pct=selected_department.contribution_pct,
            reduction_pct=reduction_pct,
        )
        existing = self.scenarios.find_equivalent(
            db,
            dataset_id=dataset_id,
            forecast_run_id=forecast_run.id,
            department=selected_department.department,
            reduction_pct=calculation["reduction_pct"],
        )
        if existing is not None:
            return existing
        return self.scenarios.create(
            db,
            {
                "dataset_id": dataset_id,
                "forecast_run_id": forecast_run.id,
                "department": selected_department.department,
                **calculation,
            },
        )

    def get(self, db: Session, scenario_id: int):
        scenario = self.scenarios.get(db, scenario_id)
        if scenario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found.")
        return scenario

    def get_latest(self, db: Session, dataset_id: int):
        scenario = self.scenarios.get_latest_for_dataset(db, dataset_id)
        if scenario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No persisted scenario found for this dataset.")
        return scenario

    @staticmethod
    def calculate(*, baseline_projected_cost: float, department_cost_share_pct: float, reduction_pct: float) -> dict[str, float]:
        department_attributable_amount = baseline_projected_cost * (department_cost_share_pct / 100)
        estimated_reduction_amount = department_attributable_amount * (reduction_pct / 100)
        scenario_projected_cost = baseline_projected_cost - estimated_reduction_amount
        impact_pct = (estimated_reduction_amount / baseline_projected_cost * 100) if baseline_projected_cost else 0.0
        return {
            "department_cost_share_pct": round(department_cost_share_pct, 2),
            "reduction_pct": round(reduction_pct, 2),
            "baseline_projected_cost": round(baseline_projected_cost, 2),
            "estimated_reduction_amount": round(estimated_reduction_amount, 2),
            "scenario_projected_cost": round(scenario_projected_cost, 2),
            "impact_pct": round(impact_pct, 2),
        }


scenario_service = ScenarioService()
