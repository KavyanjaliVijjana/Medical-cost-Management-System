from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.authentication import get_current_user
from app.db.models.user import User
from app.schemas.forecast import ForecastRequest, ForecastRunResponse
from app.services.forecast_service import forecast_service
from app.services.ownership_service import ownership_service

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post("", response_model=ForecastRunResponse)
def create_forecast(payload: ForecastRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ForecastRunResponse:
    ownership_service.require_dataset(db, current_user, payload.dataset_id)
    return forecast_service.create_forecast(db, payload.dataset_id, payload.horizon_months)


@router.get("/datasets/{dataset_id}/latest", response_model=ForecastRunResponse)
def get_latest_forecast(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ForecastRunResponse:
    ownership_service.require_dataset(db, current_user, dataset_id)
    return forecast_service.get_latest_forecast(db, dataset_id)


@router.get("/{forecast_run_id}", response_model=ForecastRunResponse)
def get_forecast(forecast_run_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ForecastRunResponse:
    ownership_service.require_forecast(db, current_user, forecast_run_id)
    return forecast_service.get_forecast(db, forecast_run_id)
