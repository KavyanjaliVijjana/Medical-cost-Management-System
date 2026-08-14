import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.authentication import get_current_user
from app.db.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import recommendation_service
from app.services.ownership_service import ownership_service

router = APIRouter(prefix="/recommendations/datasets/{dataset_id}", tags=["recommendations"])


def _response(item) -> RecommendationResponse:
    return RecommendationResponse(**{**item.__dict__, "supporting_evidence": json.loads(item.supporting_evidence)})


@router.post("/generate", response_model=list[RecommendationResponse])
def generate_recommendations(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ownership_service.require_dataset(db, current_user, dataset_id)
    return [_response(item) for item in recommendation_service.generate(db, dataset_id)]


@router.get("", response_model=list[RecommendationResponse])
def get_recommendations(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ownership_service.require_dataset(db, current_user, dataset_id)
    return [_response(item) for item in recommendation_service.list(db, dataset_id)]
