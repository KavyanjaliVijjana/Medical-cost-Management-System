from fastapi.testclient import TestClient

from app.main import app


def _processed_demo_with_forecast(client: TestClient) -> tuple[int, str]:
    validation = client.post("/api/v1/datasets/demo/validate")
    dataset_id = validation.json()["dataset"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/process")
    client.post("/api/v1/forecasts", json={"dataset_id": dataset_id, "horizon_months": 3})
    departments = client.get(f"/api/v1/analytics/datasets/{dataset_id}/summary").json()["departments"]
    return dataset_id, departments[0]["department"]


def test_scenario_api_persists_department_reduction_result() -> None:
    with TestClient(app) as client:
        dataset_id, department = _processed_demo_with_forecast(client)
        response = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": department, "reduction_pct": 10})
        payload = response.json()
        retrieved = client.get(f"/api/v1/scenarios/{payload['id']}")
        repeated = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": department, "reduction_pct": 10})
        latest = client.get(f"/api/v1/scenarios/datasets/{dataset_id}/latest")

    assert response.status_code == 200
    assert payload["department"] == department
    assert payload["baseline_projected_cost"] > 0
    assert payload["estimated_reduction_amount"] > 0
    assert round(payload["scenario_projected_cost"] + payload["estimated_reduction_amount"], 2) == payload["baseline_projected_cost"]
    assert payload["impact_pct"] == round(payload["department_cost_share_pct"] * 0.1, 2)
    assert payload["disclaimer"] == "Hypothetical estimate — not guaranteed savings."
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == payload["id"]
    assert repeated.status_code == 200
    assert repeated.json()["id"] == payload["id"]
    assert latest.status_code == 200
    assert latest.json()["id"] == payload["id"]


def test_scenario_api_rejects_invalid_percentage_and_department() -> None:
    with TestClient(app) as client:
        dataset_id, department = _processed_demo_with_forecast(client)
        for reduction_pct in (0, -1, 101):
            response = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": department, "reduction_pct": reduction_pct})
            assert response.status_code == 422
        invalid_department = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": "Unknown department", "reduction_pct": 10})

    assert invalid_department.status_code == 422
    assert "Selected department" in invalid_department.json()["detail"]


def test_scenario_api_requires_persisted_forecast() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        department = client.get(f"/api/v1/analytics/datasets/{dataset_id}/summary").json()["departments"][0]["department"]
        response = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": department, "reduction_pct": 10})

    assert response.status_code == 422
    assert "persisted forecast" in response.json()["detail"]
