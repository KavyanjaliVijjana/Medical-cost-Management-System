from fastapi.testclient import TestClient

from app.main import app


def test_forecast_api_returns_persisted_real_forecast_results() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        response = client.post("/api/v1/forecasts", json={"dataset_id": dataset_id, "horizon_months": 3})
        payload = response.json()
        retrieved = client.get(f"/api/v1/forecasts/{payload['id']}")
        latest = client.get(f"/api/v1/forecasts/datasets/{dataset_id}/latest")

    assert response.status_code == 200
    assert payload["model_name"] == "Linear Regression (monthly cost trend)"
    assert payload["horizon_months"] == 3
    assert len(payload["historical_monthly_cost"]) == 12
    assert len(payload["forecast_points"]) == 3
    assert payload["mae"] is not None
    assert payload["rmse"] is not None
    assert payload["model_comparison"]["linear_regression"]["mae"] == payload["mae"]
    assert payload["model_comparison"]["naive_last_observed"]["mae"] is not None
    assert payload["model_comparison"]["better_model"] in {
        "Linear Regression (monthly cost trend)",
        "Naive last-observed baseline",
        "Tie",
    }
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == payload["id"]
    assert latest.status_code == 200
    assert latest.json()["id"] == payload["id"]


def test_forecast_api_rejects_unsupported_horizon() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/forecasts", json={"dataset_id": 1, "horizon_months": 2})

    assert response.status_code == 422
