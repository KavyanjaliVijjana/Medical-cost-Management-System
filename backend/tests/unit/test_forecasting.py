from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.db.models.cost_record import CostRecord
from app.db.models.dataset import Dataset
from app.db.session import SessionLocal
from app.ml.forecasting import chronological_split, evaluate_naive_baseline, prepare_time_features, train_evaluate_and_forecast
from app.services.forecast_service import forecast_service


def test_feature_preparation_and_chronological_split_preserve_time_order() -> None:
    features = prepare_time_features(4, start_index=3)
    x_train, x_test, y_train, y_test = chronological_split([100, 110, 120, 130, 140, 150, 160, 170, 180, 190])

    assert features.flatten().tolist() == [3, 4, 5, 6]
    assert x_train.flatten().tolist() == list(range(8))
    assert x_test.flatten().tolist() == [8, 9]
    assert y_train.tolist() == [100, 110, 120, 130, 140, 150, 160, 170]
    assert y_test.tolist() == [180, 190]


def test_linear_regression_trains_evaluates_and_generates_future_costs() -> None:
    result = train_evaluate_and_forecast([100, 110, 120, 130, 140, 150, 160, 170, 180, 190], 3)

    assert result.evaluation.mae == 0
    assert result.evaluation.rmse == 0
    assert result.evaluation.r_squared == 1
    assert result.naive_evaluation.mae == 10
    assert result.naive_evaluation.rmse == 10
    assert result.future_values == [200, 210, 220]


def test_naive_baseline_uses_the_latest_observed_value_for_each_holdout_step() -> None:
    result = evaluate_naive_baseline([100, 110, 120, 130, 140, 150, 160, 170, 180, 190])

    assert result.mae == 10
    assert result.rmse == 10
    assert result.r_squared is None


def test_r_squared_is_not_reported_when_only_one_test_month_exists() -> None:
    result = train_evaluate_and_forecast([100, 110, 120, 130], 1)

    assert result.evaluation.r_squared is None


def test_insufficient_months_do_not_generate_a_forecast() -> None:
    with pytest.raises(ValueError, match="At least 4 months"):
        chronological_split([100, 110, 120])


def test_forecast_service_rejects_dataset_with_insufficient_months() -> None:
    db: Session = SessionLocal()
    try:
        dataset = Dataset(name="Short", source_type="uploaded", is_synthetic=False, row_count=3, processing_status="completed")
        db.add(dataset)
        db.flush()
        db.add_all([
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 1, 1), department="Cardiology", patient_count=10, total_cost=100),
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 2, 1), department="Cardiology", patient_count=10, total_cost=110),
            CostRecord(dataset_id=dataset.id, record_date=date(2025, 3, 1), department="Cardiology", patient_count=10, total_cost=120),
        ])
        db.commit()
        with pytest.raises(Exception, match="At least 4 months"):
            forecast_service.create_forecast(db, dataset.id, 3)
    finally:
        db.close()
