from collections import defaultdict
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.forecast_run import ForecastRun
from app.ml.forecasting import (
    MODEL_NAME,
    NAIVE_MODEL_NAME,
    MINIMUM_MONTHS,
    evaluate_naive_baseline,
    next_month_starts,
    train_evaluate_and_forecast,
)
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.schemas.forecast import ForecastModelComparison, ForecastModelMetrics, ForecastRunResponse, HistoricalCostPoint


class ForecastService:
    """Creates persisted, explainable monthly-cost Linear Regression forecasts."""

    def __init__(self) -> None:
        self.datasets = DatasetRepository()
        self.forecasts = ForecastRepository()

    def create_forecast(self, db: Session, dataset_id: int, horizon_months: int) -> ForecastRunResponse:
        if horizon_months not in {1, 3, 6, 12}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Forecast horizon must be 1, 3, 6, or 12 months.")
        dataset = self.datasets.get_dataset(db, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        if dataset.processing_status != "completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only completed datasets can be forecast.")

        historical = self._monthly_costs(db, dataset_id)
        if len(historical) < MINIMUM_MONTHS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"At least {MINIMUM_MONTHS} months of historical cost data are required for forecasting.",
            )
        baseline = train_evaluate_and_forecast([point.total_cost for point in historical], horizon_months)
        future_months = next_month_starts(historical[-1].month, horizon_months)
        run = self.forecasts.create_run(
            db,
            dataset_id=dataset_id,
            horizon_months=horizon_months,
            model_name=MODEL_NAME,
            mae=baseline.evaluation.mae,
            rmse=baseline.evaluation.rmse,
            r_squared=baseline.evaluation.r_squared,
            points=[
                {"forecast_month": month, "predicted_cost": predicted_cost}
                for month, predicted_cost in zip(future_months, baseline.future_values, strict=True)
            ],
        )
        return self._serialize_run(dataset, run, historical)

    def get_forecast(self, db: Session, run_id: int) -> ForecastRunResponse:
        run = self.forecasts.get_run(db, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast run not found.")
        dataset = self.datasets.get_dataset(db, run.dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return self._serialize_run(dataset, run, self._monthly_costs(db, run.dataset_id))

    def get_latest_forecast(self, db: Session, dataset_id: int) -> ForecastRunResponse:
        run = self.forecasts.get_latest_for_dataset(db, dataset_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No persisted forecast found for this dataset.")
        dataset = self.datasets.get_dataset(db, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return self._serialize_run(dataset, run, self._monthly_costs(db, dataset_id))

    def _monthly_costs(self, db: Session, dataset_id: int) -> list[HistoricalCostPoint]:
        totals: dict[date, float] = defaultdict(float)
        for record in self.datasets.list_all_records(db, dataset_id):
            month = record.record_date.replace(day=1)
            totals[month] += record.total_cost
        return [HistoricalCostPoint(month=month, total_cost=round(totals[month], 2)) for month in sorted(totals)]

    def _serialize_run(self, dataset, run: ForecastRun, historical: list[HistoricalCostPoint]) -> ForecastRunResponse:
        points = sorted(run.points, key=lambda point: point.forecast_month)
        expected_change_pct: float | None = None
        if historical and points and historical[-1].total_cost != 0:
            expected_change_pct = round(((points[-1].predicted_cost - historical[-1].total_cost) / historical[-1].total_cost) * 100, 2)
        return ForecastRunResponse(
            id=run.id,
            dataset_id=run.dataset_id,
            horizon_months=run.horizon_months,
            model_name=run.model_name,
            mae=run.mae,
            rmse=run.rmse,
            r_squared=run.r_squared,
            created_at=run.created_at,
            expected_change_pct=expected_change_pct,
            model_comparison=self._model_comparison(historical, run),
            historical_monthly_cost=historical,
            forecast_points=points,
            dataset=dataset,
        )

    def _model_comparison(self, historical: list[HistoricalCostPoint], run: ForecastRun) -> ForecastModelComparison:
        naive = evaluate_naive_baseline([point.total_cost for point in historical])
        linear = ForecastModelMetrics(
            model_name=run.model_name,
            mae=run.mae,
            rmse=run.rmse,
            r_squared=run.r_squared,
        )
        naive_metrics = ForecastModelMetrics(
            model_name=NAIVE_MODEL_NAME,
            mae=naive.mae,
            rmse=naive.rmse,
        )
        if linear.mae is None or linear.rmse is None:
            better_model = NAIVE_MODEL_NAME
        elif linear.mae < naive.mae or (linear.mae == naive.mae and linear.rmse < naive.rmse):
            better_model = MODEL_NAME
        elif linear.mae == naive.mae and linear.rmse == naive.rmse:
            better_model = "Tie"
        else:
            better_model = NAIVE_MODEL_NAME
        return ForecastModelComparison(
            linear_regression=linear,
            naive_last_observed=naive_metrics,
            better_model=better_model,
        )


forecast_service = ForecastService()
