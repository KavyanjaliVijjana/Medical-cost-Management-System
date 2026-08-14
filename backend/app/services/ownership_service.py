"""Dataset ownership checks applied before deterministic services receive a dataset id."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.scenario_repository import ScenarioRepository


class OwnershipService:
    def __init__(self) -> None:
        self.datasets = DatasetRepository()
        self.forecasts = ForecastRepository()
        self.scenarios = ScenarioRepository()

    def require_dataset(self, db: Session, user: User, dataset_id: int):
        dataset = self.datasets.get_dataset(db, dataset_id)
        if dataset is None or dataset.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return dataset

    def require_forecast(self, db: Session, user: User, forecast_run_id: int):
        forecast = self.forecasts.get_run(db, forecast_run_id)
        if forecast is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found.")
        self.require_dataset(db, user, forecast.dataset_id)
        return forecast

    def require_scenario(self, db: Session, user: User, scenario_id: int):
        scenario = self.scenarios.get(db, scenario_id)
        if scenario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found.")
        self.require_dataset(db, user, scenario.dataset_id)
        return scenario


ownership_service = OwnershipService()
