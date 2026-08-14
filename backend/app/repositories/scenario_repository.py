from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.scenario_run import ScenarioRun


class ScenarioRepository:
    """Persistence boundary for transparent what-if scenario runs."""

    def create(self, db: Session, values: dict[str, object]) -> ScenarioRun:
        scenario = ScenarioRun(**values)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    def get(self, db: Session, scenario_id: int) -> ScenarioRun | None:
        return db.get(ScenarioRun, scenario_id)

    def get_latest_for_dataset(self, db: Session, dataset_id: int) -> ScenarioRun | None:
        statement = (
            select(ScenarioRun)
            .where(ScenarioRun.dataset_id == dataset_id)
            .order_by(ScenarioRun.created_at.desc(), ScenarioRun.id.desc())
        )
        return db.scalar(statement)

    def find_equivalent(
        self, db: Session, *, dataset_id: int, forecast_run_id: int, department: str, reduction_pct: float
    ) -> ScenarioRun | None:
        statement = select(ScenarioRun).where(
            ScenarioRun.dataset_id == dataset_id,
            ScenarioRun.forecast_run_id == forecast_run_id,
            ScenarioRun.department == department,
            ScenarioRun.reduction_pct == reduction_pct,
        )
        return db.scalar(statement)
