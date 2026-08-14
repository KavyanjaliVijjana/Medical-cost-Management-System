from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.dataset import DatasetResponse


class ForecastRequest(BaseModel):
    dataset_id: int
    horizon_months: int = Field(default=3, ge=1, le=12)

    @field_validator("horizon_months")
    @classmethod
    def supported_horizon(cls, value: int) -> int:
        if value not in {1, 3, 6, 12}:
            raise ValueError("Forecast horizon must be 1, 3, 6, or 12 months.")
        return value


class HistoricalCostPoint(BaseModel):
    month: date
    total_cost: float


class ForecastPointResponse(BaseModel):
    forecast_month: date
    predicted_cost: float

    model_config = {"from_attributes": True}


class ForecastModelMetrics(BaseModel):
    model_name: str
    mae: float | None
    rmse: float | None
    r_squared: float | None = None


class ForecastModelComparison(BaseModel):
    linear_regression: ForecastModelMetrics
    naive_last_observed: ForecastModelMetrics
    better_model: str


class ForecastRunResponse(BaseModel):
    id: int
    dataset_id: int
    horizon_months: int
    model_name: str
    mae: float | None
    rmse: float | None
    r_squared: float | None
    created_at: datetime
    expected_change_pct: float | None
    model_comparison: ForecastModelComparison
    historical_monthly_cost: list[HistoricalCostPoint]
    forecast_points: list[ForecastPointResponse]
    dataset: DatasetResponse
