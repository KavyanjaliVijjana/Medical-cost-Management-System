from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.authentication import get_current_user
from app.db.models.user import User
from app.schemas.scenario import ScenarioRequest, ScenarioResponse
from app.services.scenario_service import scenario_service
from app.services.ownership_service import ownership_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioResponse)
def create_scenario(payload: ScenarioRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioResponse:
    ownership_service.require_dataset(db, current_user, payload.dataset_id)
    return scenario_service.create(
        db,
        dataset_id=payload.dataset_id,
        department=payload.department,
        reduction_pct=payload.reduction_pct,
    )


@router.get("/datasets/{dataset_id}/latest", response_model=ScenarioResponse)
def get_latest_scenario(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioResponse:
    ownership_service.require_dataset(db, current_user, dataset_id)
    return scenario_service.get_latest(db, dataset_id)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioResponse:
    ownership_service.require_scenario(db, current_user, scenario_id)
    return scenario_service.get(db, scenario_id)
