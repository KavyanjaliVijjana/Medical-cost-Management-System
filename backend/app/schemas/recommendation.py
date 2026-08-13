from datetime import datetime

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    id: int
    dataset_id: int
    title: str
    category: str
    priority: str
    rationale: str
    supporting_evidence: list[str]
    triggering_metric: str
    period: str
    created_at: datetime

    model_config = {"from_attributes": True}
