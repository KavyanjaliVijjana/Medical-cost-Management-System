from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    row: int | None = None
    field: str | None = None
    code: str
    message: str


class ValidationSummary(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    validation_errors: list[ValidationErrorItem]
    is_valid: bool


class DatasetResponse(BaseModel):
    id: int
    name: str
    source_type: str
    is_synthetic: bool
    uploaded_at: datetime
    row_count: int
    processing_status: str

    model_config = {"from_attributes": True}


class DatasetValidationResponse(BaseModel):
    dataset: DatasetResponse | None = None
    validation: ValidationSummary
    preview: list[dict[str, Any]] = Field(default_factory=list)


class CostRecordResponse(BaseModel):
    id: int
    dataset_id: int
    record_date: date
    department: str
    patient_count: int
    total_cost: float
    service_type: str | None = None
    medicine_cost: float | None = None
    lab_cost: float | None = None
    treatment_cost: float | None = None
    insurance_amount: float | None = None
    provider_type: str | None = None
    site_of_care: str | None = None
    drug_category: str | None = None
    unit_cost: float | None = None

    model_config = {"from_attributes": True}


class DatasetPreviewResponse(BaseModel):
    dataset: DatasetResponse
    records: list[CostRecordResponse]
