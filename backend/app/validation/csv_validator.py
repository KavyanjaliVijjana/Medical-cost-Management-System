import csv
import io
import math
from datetime import date
from typing import Any

from app.schemas.dataset import ValidationErrorItem, ValidationSummary

REQUIRED_COLUMNS = ("date", "department", "patient_count", "total_cost")
OPTIONAL_COLUMNS = (
    "service_type",
    "medicine_cost",
    "lab_cost",
    "treatment_cost",
    "insurance_amount",
    "provider_type",
    "site_of_care",
    "drug_category",
    "unit_cost",
)
NUMERIC_OPTIONAL_COLUMNS = {
    "medicine_cost",
    "lab_cost",
    "treatment_cost",
    "insurance_amount",
    "unit_cost",
}


class CsvValidationResult:
    def __init__(self, summary: ValidationSummary, records: list[dict[str, Any]]) -> None:
        self.summary = summary
        self.records = records


def validate_csv_bytes(content: bytes, filename: str | None, content_type: str | None) -> CsvValidationResult:
    errors: list[ValidationErrorItem] = []
    if not filename or not filename.lower().endswith(".csv"):
        return CsvValidationResult(_file_error("invalid_file_type", "Please upload a file with a .csv extension."), [])
    if content_type and content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}:
        return CsvValidationResult(_file_error("invalid_file_type", "The uploaded file is not recognized as CSV."), [])

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return CsvValidationResult(_file_error("invalid_encoding", "CSV files must use UTF-8 encoding."), [])

    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing_columns:
            return CsvValidationResult(
                _file_error("missing_required_columns", f"Missing required column(s): {', '.join(missing_columns)}."), []
            )
        raw_rows = list(reader)
    except csv.Error as error:
        return CsvValidationResult(_file_error("invalid_csv", f"Unable to parse CSV: {error}"), [])

    if not raw_rows:
        return CsvValidationResult(_file_error("empty_file", "The CSV contains no data rows."), [])

    valid_records: list[dict[str, Any]] = []
    seen_records: set[tuple[tuple[str, str], ...]] = set()
    invalid_row_numbers: set[int] = set()
    duplicate_rows = 0

    accepted_columns = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
    for row_number, raw_row in enumerate(raw_rows, start=2):
        normalized, row_errors = _normalize_row(raw_row, accepted_columns, row_number)
        if row_errors:
            errors.extend(row_errors)
            invalid_row_numbers.add(row_number)
            continue

        duplicate_key = tuple(sorted((key, str(value)) for key, value in normalized.items()))
        if duplicate_key in seen_records:
            duplicate_rows += 1
            invalid_row_numbers.add(row_number)
            errors.append(
                ValidationErrorItem(
                    row=row_number,
                    code="duplicate_record",
                    message="This record duplicates an earlier row in the file.",
                )
            )
            continue
        seen_records.add(duplicate_key)
        valid_records.append(normalized)

    summary = ValidationSummary(
        total_rows=len(raw_rows),
        valid_rows=len(valid_records),
        invalid_rows=len(invalid_row_numbers),
        duplicate_rows=duplicate_rows,
        validation_errors=errors,
        is_valid=not errors,
    )
    return CsvValidationResult(summary, valid_records)


def _file_error(code: str, message: str) -> ValidationSummary:
    return ValidationSummary(
        total_rows=0,
        valid_rows=0,
        invalid_rows=0,
        duplicate_rows=0,
        validation_errors=[ValidationErrorItem(code=code, message=message)],
        is_valid=False,
    )


def _normalize_row(
    raw_row: dict[str, str | None], accepted_columns: set[str], row_number: int
) -> tuple[dict[str, Any], list[ValidationErrorItem]]:
    errors: list[ValidationErrorItem] = []
    record: dict[str, Any] = {}
    for column in REQUIRED_COLUMNS:
        value = raw_row.get(column)
        if value is None or not value.strip():
            errors.append(ValidationErrorItem(row=row_number, field=column, code="missing_value", message=f"{column} is required."))

    if errors:
        return record, errors

    date_value = _parse_date(raw_row["date"], row_number, errors)
    patient_count = _parse_patient_count(raw_row["patient_count"], row_number, errors)
    total_cost = _parse_nonnegative_number(raw_row["total_cost"], "total_cost", row_number, errors)
    if date_value is None or patient_count is None or total_cost is None:
        return record, errors

    record = {
        "record_date": date_value,
        "department": raw_row["department"].strip(),
        "patient_count": patient_count,
        "total_cost": total_cost,
    }
    for column in OPTIONAL_COLUMNS:
        if column not in accepted_columns:
            continue
        raw_value = raw_row.get(column)
        if raw_value is None or not raw_value.strip():
            continue
        if column in NUMERIC_OPTIONAL_COLUMNS:
            value = _parse_nonnegative_number(raw_value, column, row_number, errors)
            if value is not None:
                record[column] = value
        else:
            record[column] = raw_value.strip()
    return record, errors


def _parse_date(value: str, row_number: int, errors: list[ValidationErrorItem]) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        errors.append(ValidationErrorItem(row=row_number, field="date", code="invalid_date", message="date must use YYYY-MM-DD format."))
        return None


def _parse_patient_count(value: str, row_number: int, errors: list[ValidationErrorItem]) -> int | None:
    parsed = _parse_nonnegative_number(value, "patient_count", row_number, errors)
    if parsed is None:
        return None
    if not parsed.is_integer():
        errors.append(ValidationErrorItem(row=row_number, field="patient_count", code="invalid_numeric", message="patient_count must be a whole number."))
        return None
    return int(parsed)


def _parse_nonnegative_number(
    value: str, field: str, row_number: int, errors: list[ValidationErrorItem]
) -> float | None:
    try:
        parsed = float(value.strip())
    except ValueError:
        errors.append(ValidationErrorItem(row=row_number, field=field, code="invalid_numeric", message=f"{field} must be numeric."))
        return None
    if not math.isfinite(parsed):
        errors.append(ValidationErrorItem(row=row_number, field=field, code="invalid_numeric", message=f"{field} must be finite."))
        return None
    if parsed < 0:
        errors.append(ValidationErrorItem(row=row_number, field=field, code="negative_value", message=f"{field} cannot be negative."))
        return None
    return parsed
