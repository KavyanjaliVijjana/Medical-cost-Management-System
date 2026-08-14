from datetime import datetime

from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    dataset_id: int
    department: str = Field(min_length=1, max_length=255)
    reduction_pct: float = Field(gt=0, le=100)


class ScenarioResponse(BaseModel):
    id: int
    dataset_id: int
    forecast_run_id: int
    department: str
    department_cost_share_pct: float
    reduction_pct: float
    baseline_projected_cost: float
    estimated_reduction_amount: float
    scenario_projected_cost: float
    impact_pct: float
    created_at: datetime
    disclaimer: str = "Hypothetical estimate — not guaranteed savings."

    model_config = {"from_attributes": True}
