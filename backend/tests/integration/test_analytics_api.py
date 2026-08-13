from fastapi.testclient import TestClient

from app.main import app


def test_analytics_endpoint_returns_persisted_dataset_values() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        response = client.get(f"/api/v1/analytics/datasets/{dataset_id}/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset"]["id"] == dataset_id
    assert payload["metrics"]["total_medical_cost"] > 0
    assert payload["metrics"]["total_patient_count"] > 0
    assert len(payload["monthly_trend"]) == 12
    assert len(payload["departments"]) == 5
