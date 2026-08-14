from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.forecast_point import ForecastPoint
from app.db.models.forecast_run import ForecastRun


class ForecastRepository:
    """Persistence boundary for reproducible forecast runs and forecast points."""

    def create_run(
        self,
        db: Session,
        *,
        dataset_id: int,
        horizon_months: int,
        model_name: str,
        mae: float | None,
        rmse: float | None,
        r_squared: float | None,
        points: list[dict[str, object]],
    ) -> ForecastRun:
        run = ForecastRun(
            dataset_id=dataset_id,
            horizon_months=horizon_months,
            model_name=model_name,
            mae=mae,
            rmse=rmse,
            r_squared=r_squared,
        )
        db.add(run)
        db.flush()
        db.add_all([ForecastPoint(forecast_run_id=run.id, **point) for point in points])
        db.commit()
        return self.get_run(db, run.id)  # type: ignore[return-value]

    def get_run(self, db: Session, run_id: int) -> ForecastRun | None:
        statement = (
            select(ForecastRun)
            .where(ForecastRun.id == run_id)
            .options(selectinload(ForecastRun.points))
        )
        return db.scalar(statement)

    def get_latest_for_dataset(self, db: Session, dataset_id: int) -> ForecastRun | None:
        statement = (
            select(ForecastRun)
            .where(ForecastRun.dataset_id == dataset_id)
            .order_by(ForecastRun.created_at.desc(), ForecastRun.id.desc())
            .options(selectinload(ForecastRun.points))
        )
        return db.scalar(statement)
