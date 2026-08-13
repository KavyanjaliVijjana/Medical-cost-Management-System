from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/datasets/{dataset_id}/summary", response_model=AnalyticsSummaryResponse)
def get_dataset_analytics(dataset_id: int, db: Session = Depends(get_db)) -> AnalyticsSummaryResponse:
    return analytics_service.get_summary(db, dataset_id)
