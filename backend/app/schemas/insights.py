from datetime import datetime

from pydantic import BaseModel


class DriverInsightResponse(BaseModel):
    id: int
    dataset_id: int
    metric: str
    observed_value: float
    baseline_value: float | None
    change_pct: float | None
    period: str
    explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    dataset_id: int
    severity: str
    metric: str
    observed_value: float
    threshold_value: float
    period: str
    explanation: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
