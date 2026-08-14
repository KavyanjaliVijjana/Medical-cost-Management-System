from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.advisor_agent import medical_economics_advisor
from app.db.session import get_db
from app.schemas.advisor import AdvisorRequest, AdvisorResponse

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/ask", response_model=AdvisorResponse)
def ask_medical_economics_advisor(payload: AdvisorRequest, db: Session = Depends(get_db)) -> AdvisorResponse:
    return medical_economics_advisor.answer(db, dataset_id=payload.dataset_id, question=payload.question)
