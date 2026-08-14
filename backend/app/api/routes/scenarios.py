from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.scenario import ScenarioRequest, ScenarioResponse
from app.services.scenario_service import scenario_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioResponse)
def create_scenario(payload: ScenarioRequest, db: Session = Depends(get_db)) -> ScenarioResponse:
    return scenario_service.create(
        db,
        dataset_id=payload.dataset_id,
        department=payload.department,
        reduction_pct=payload.reduction_pct,
    )


@router.get("/datasets/{dataset_id}/latest", response_model=ScenarioResponse)
def get_latest_scenario(dataset_id: int, db: Session = Depends(get_db)) -> ScenarioResponse:
    return scenario_service.get_latest(db, dataset_id)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)) -> ScenarioResponse:
    return scenario_service.get(db, scenario_id)
