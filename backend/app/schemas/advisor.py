from typing import Any, Literal

from pydantic import BaseModel, Field


class AdvisorRequest(BaseModel):
    dataset_id: int
    question: str = Field(min_length=3, max_length=2000)


class AdvisorToolEvidenceResponse(BaseModel):
    tool: str
    result: dict[str, Any] | None = None
    error: str | None = None

    model_config = {"from_attributes": True}


class AdvisorResponse(BaseModel):
    dataset_id: int
    question: str
    status: Literal["completed", "provider_unavailable", "provider_error", "unsupported_question"]
    answer: str | None
    message: str | None
    tools_used: list[str]
    evidence: list[AdvisorToolEvidenceResponse]
    provider: str
    model: str | None
