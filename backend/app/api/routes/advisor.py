from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.advisor_agent import medical_economics_advisor
from app.db.session import get_db
from app.core.authentication import get_current_user
from app.db.models.user import User
from app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.services.advisor_tool_executor import ControlledAdvisorToolExecutor
from app.services.ownership_service import ownership_service

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/ask", response_model=AdvisorResponse)
def ask_medical_economics_advisor(payload: AdvisorRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AdvisorResponse:
    ownership_service.require_dataset(db, current_user, payload.dataset_id)
    return medical_economics_advisor.answer(
        executor=ControlledAdvisorToolExecutor(db),
        dataset_id=payload.dataset_id,
        question=payload.question,
    )
