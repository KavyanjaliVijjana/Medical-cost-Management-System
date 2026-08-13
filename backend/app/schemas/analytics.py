from pydantic import BaseModel

from app.schemas.dataset import DatasetResponse


class OverallMetrics(BaseModel):
    total_medical_cost: float
    total_patient_count: int
    average_monthly_cost: float | None
    average_monthly_patient_count: float | None
    cost_per_patient: float | None
    latest_month: str | None
    latest_month_cost: float | None
    previous_month: str | None
    previous_month_cost: float | None
    month_over_month_cost_change_pct: float | None


class MonthlyTrendPoint(BaseModel):
    month: str
    total_cost: float
    patient_count: int
    cost_per_patient: float | None
    month_over_month_cost_change_pct: float | None


class DepartmentAnalytics(BaseModel):
    department: str
    total_cost: float
    patient_count: int
    cost_per_patient: float | None
    contribution_pct: float | None


class AnalyticsSummaryResponse(BaseModel):
    dataset: DatasetResponse
    metrics: OverallMetrics
    monthly_trend: list[MonthlyTrendPoint]
    departments: list[DepartmentAnalytics]
    highest_cost_department: DepartmentAnalytics | None
