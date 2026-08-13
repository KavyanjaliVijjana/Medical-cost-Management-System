from datetime import date

from sqlalchemy.orm import Session

from app.db.models.cost_record import CostRecord
from app.db.models.dataset import Dataset
from app.db.session import SessionLocal
from app.services.analytics_service import analytics_service


def create_dataset_with_records(db: Session) -> Dataset:
    dataset = Dataset(
        name="Analytics test dataset",
        source_type="uploaded",
        is_synthetic=False,
        row_count=4,
        processing_status="completed",
    )
    db.add(dataset)
    db.flush()
    db.add_all(
        [
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 1, 1), department="Cardiology", patient_count=10, total_cost=100),
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 1, 15), department="Emergency", patient_count=5, total_cost=50),
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 2, 1), department="Cardiology", patient_count=20, total_cost=200),
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 2, 14), department="Emergency", patient_count=10, total_cost=100),
        ]
    )
    db.commit()
    db.refresh(dataset)
    return dataset


def test_overall_metrics_calculate_total_patients_and_cost_per_patient() -> None:
    db = SessionLocal()
    try:
        summary = analytics_service.get_summary(db, create_dataset_with_records(db).id)
    finally:
        db.close()

    assert summary.metrics.total_medical_cost == 450
    assert summary.metrics.total_patient_count == 45
    assert summary.metrics.cost_per_patient == 10
    assert summary.metrics.average_monthly_cost == 225
    assert summary.metrics.average_monthly_patient_count == 22.5


def test_monthly_aggregation_and_month_over_month_change_are_chronological() -> None:
    db = SessionLocal()
    try:
        summary = analytics_service.get_summary(db, create_dataset_with_records(db).id)
    finally:
        db.close()

    assert [(point.month, point.total_cost, point.patient_count) for point in summary.monthly_trend] == [
        ("2025-01", 150, 15),
        ("2025-02", 300, 30),
    ]
    assert summary.monthly_trend[0].month_over_month_cost_change_pct is None
    assert summary.monthly_trend[1].month_over_month_cost_change_pct == 100
    assert summary.metrics.month_over_month_cost_change_pct == 100


def test_department_totals_contribution_and_highest_cost_department() -> None:
    db = SessionLocal()
    try:
        summary = analytics_service.get_summary(db, create_dataset_with_records(db).id)
    finally:
        db.close()

    assert summary.highest_cost_department is not None
    assert summary.highest_cost_department.department == "Cardiology"
    assert summary.departments[0].total_cost == 300
    assert summary.departments[0].patient_count == 30
    assert summary.departments[0].cost_per_patient == 10
    assert summary.departments[0].contribution_pct == 66.67
    assert summary.departments[1].contribution_pct == 33.33


def test_empty_and_single_month_datasets_are_handled_without_division_errors() -> None:
    db = SessionLocal()
    try:
        empty = Dataset(name="Empty", source_type="uploaded", is_synthetic=False, row_count=0, processing_status="completed")
        db.add(empty)
        db.commit()
        empty_summary = analytics_service.get_summary(db, empty.id)

        single = Dataset(name="Single", source_type="uploaded", is_synthetic=False, row_count=1, processing_status="completed")
        db.add(single)
        db.flush()
        db.add(CostRecord(dataset_id=single.id, record_date=date(2025, 3, 1), department="Zero", patient_count=0, total_cost=100))
        db.commit()
        single_summary = analytics_service.get_summary(db, single.id)
    finally:
        db.close()

    assert empty_summary.metrics.total_medical_cost == 0
    assert empty_summary.metrics.cost_per_patient is None
    assert empty_summary.monthly_trend == []
    assert empty_summary.highest_cost_department is None
    assert single_summary.metrics.month_over_month_cost_change_pct is None
    assert single_summary.metrics.cost_per_patient is None
