from app.validation.csv_validator import validate_csv_bytes


def validate(content: str):
    return validate_csv_bytes(content.encode("utf-8"), "costs.csv", "text/csv")


def test_valid_csv_is_accepted() -> None:
    result = validate("date,department,patient_count,total_cost\n2025-01-01,Cardiology,25,1200.50\n")

    assert result.summary.is_valid is True
    assert result.summary.valid_rows == 1
    assert result.records[0]["record_date"].isoformat() == "2025-01-01"


def test_missing_required_column_is_rejected() -> None:
    result = validate("date,department,total_cost\n2025-01-01,Cardiology,1200\n")

    assert result.summary.is_valid is False
    assert result.summary.validation_errors[0].code == "missing_required_columns"


def test_invalid_date_is_rejected() -> None:
    result = validate("date,department,patient_count,total_cost\nnot-a-date,Cardiology,25,1200\n")

    assert result.summary.validation_errors[0].code == "invalid_date"


def test_invalid_numeric_value_is_rejected() -> None:
    result = validate("date,department,patient_count,total_cost\n2025-01-01,Cardiology,twenty,1200\n")

    assert result.summary.validation_errors[0].code == "invalid_numeric"


def test_negative_value_is_rejected() -> None:
    result = validate("date,department,patient_count,total_cost\n2025-01-01,Cardiology,-1,1200\n")

    assert result.summary.validation_errors[0].code == "negative_value"


def test_duplicate_records_are_rejected() -> None:
    content = "date,department,patient_count,total_cost\n2025-01-01,Cardiology,25,1200\n2025-01-01,Cardiology,25,1200\n"
    result = validate(content)

    assert result.summary.is_valid is False
    assert result.summary.duplicate_rows == 1
    assert result.summary.validation_errors[0].code == "duplicate_record"
