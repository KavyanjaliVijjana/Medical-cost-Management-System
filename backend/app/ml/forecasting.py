from dataclasses import dataclass
from datetime import date
from math import ceil

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


MODEL_NAME = "Linear Regression (monthly cost trend)"
NAIVE_MODEL_NAME = "Naive last-observed baseline"
MINIMUM_MONTHS = 4


@dataclass(frozen=True)
class ForecastEvaluation:
    mae: float
    rmse: float
    r_squared: float | None


@dataclass(frozen=True)
class BaselineForecast:
    evaluation: ForecastEvaluation
    naive_evaluation: ForecastEvaluation
    future_values: list[float]


def prepare_time_features(month_count: int, start_index: int = 0) -> np.ndarray:
    """Return a chronological month-index feature matrix; no observations are shuffled."""
    return np.arange(start_index, start_index + month_count, dtype=float).reshape(-1, 1)


def chronological_split(monthly_costs: list[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split ordered observations with the final 20% reserved for validation."""
    if len(monthly_costs) < MINIMUM_MONTHS:
        raise ValueError(f"At least {MINIMUM_MONTHS} months of historical cost data are required.")
    test_count = max(1, ceil(len(monthly_costs) * 0.2))
    train_count = len(monthly_costs) - test_count
    if train_count < 2:
        raise ValueError("At least two chronological training months are required.")
    features = prepare_time_features(len(monthly_costs))
    targets = np.asarray(monthly_costs, dtype=float)
    return features[:train_count], features[train_count:], targets[:train_count], targets[train_count:]


def train_evaluate_and_forecast(monthly_costs: list[float], horizon_months: int) -> BaselineForecast:
    """Evaluate on the latest chronological holdout, then fit all history for future predictions."""
    x_train, x_test, y_train, y_test = chronological_split(monthly_costs)
    evaluation_model = LinearRegression().fit(x_train, y_train)
    test_predictions = evaluation_model.predict(x_test)
    evaluation = _evaluate(y_test, test_predictions, include_r_squared=True)
    naive_evaluation = evaluate_naive_baseline(monthly_costs)
    final_model = LinearRegression().fit(prepare_time_features(len(monthly_costs)), np.asarray(monthly_costs, dtype=float))
    future_features = prepare_time_features(horizon_months, start_index=len(monthly_costs))
    future_values = [round(max(0.0, float(value)), 2) for value in final_model.predict(future_features)]
    return BaselineForecast(evaluation=evaluation, naive_evaluation=naive_evaluation, future_values=future_values)


def evaluate_naive_baseline(monthly_costs: list[float]) -> ForecastEvaluation:
    """Evaluate a one-step persistence baseline on the same chronological holdout."""
    _, _, y_train, y_test = chronological_split(monthly_costs)
    predictions = np.concatenate(([y_train[-1]], y_test[:-1]))
    return _evaluate(y_test, predictions, include_r_squared=False)


def _evaluate(actual: np.ndarray, predicted: np.ndarray, *, include_r_squared: bool) -> ForecastEvaluation:
    return ForecastEvaluation(
        mae=round(float(mean_absolute_error(actual, predicted)), 2),
        rmse=round(float(mean_squared_error(actual, predicted) ** 0.5), 2),
        r_squared=round(float(r2_score(actual, predicted)), 4) if include_r_squared and len(actual) >= 2 else None,
    )


def next_month_starts(last_month: date, horizon_months: int) -> list[date]:
    months: list[date] = []
    year, month = last_month.year, last_month.month
    for _ in range(horizon_months):
        month += 1
        if month == 13:
            year += 1
            month = 1
        months.append(date(year, month, 1))
    return months
