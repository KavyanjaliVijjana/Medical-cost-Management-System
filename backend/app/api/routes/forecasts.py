from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.forecast import ForecastRequest, ForecastRunResponse
from app.services.forecast_service import forecast_service

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post("", response_model=ForecastRunResponse)
def create_forecast(payload: ForecastRequest, db: Session = Depends(get_db)) -> ForecastRunResponse:
    return forecast_service.create_forecast(db, payload.dataset_id, payload.horizon_months)


@router.get("/{forecast_run_id}", response_model=ForecastRunResponse)
def get_forecast(forecast_run_id: int, db: Session = Depends(get_db)) -> ForecastRunResponse:
    return forecast_service.get_forecast(db, forecast_run_id)
