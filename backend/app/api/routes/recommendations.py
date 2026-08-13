import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations/datasets/{dataset_id}", tags=["recommendations"])


def _response(item) -> RecommendationResponse:
    return RecommendationResponse(**{**item.__dict__, "supporting_evidence": json.loads(item.supporting_evidence)})


@router.post("/generate", response_model=list[RecommendationResponse])
def generate_recommendations(dataset_id: int, db: Session = Depends(get_db)):
    return [_response(item) for item in recommendation_service.generate(db, dataset_id)]


@router.get("", response_model=list[RecommendationResponse])
def get_recommendations(dataset_id: int, db: Session = Depends(get_db)):
    return [_response(item) for item in recommendation_service.list(db, dataset_id)]
