from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.authentication import get_current_user
from app.db.models.user import User
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import analytics_service
from app.services.ownership_service import ownership_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/datasets/{dataset_id}/summary", response_model=AnalyticsSummaryResponse)
def get_dataset_analytics(dataset_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AnalyticsSummaryResponse:
    ownership_service.require_dataset(db, current_user, dataset_id)
    return analytics_service.get_summary(db, dataset_id)
