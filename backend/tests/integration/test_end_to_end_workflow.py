from fastapi.testclient import TestClient

from app.main import app


def test_demo_dataset_end_to_end_cost_containment_workflow() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        processed = client.post(f"/api/v1/datasets/{dataset_id}/process")
        analytics = client.get(f"/api/v1/analytics/datasets/{dataset_id}/summary")
        forecast = client.post("/api/v1/forecasts", json={"dataset_id": dataset_id, "horizon_months": 3})
        drivers = client.post(f"/api/v1/insights/datasets/{dataset_id}/drivers/generate")
        alerts = client.post(f"/api/v1/insights/datasets/{dataset_id}/alerts/generate")
        recommendations = client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate")
        department = analytics.json()["highest_cost_department"]["department"]
        scenario = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": department, "reduction_pct": 5})
        latest_forecast = client.get(f"/api/v1/forecasts/datasets/{dataset_id}/latest")
        latest_scenario = client.get(f"/api/v1/scenarios/datasets/{dataset_id}/latest")

    assert processed.status_code == 200
    assert analytics.status_code == 200
    assert forecast.status_code == 200
    assert len(drivers.json()) > 0
    assert alerts.status_code == 200
    assert recommendations.status_code == 200
    assert scenario.status_code == 200
    assert latest_forecast.json()["id"] == forecast.json()["id"]
    assert latest_scenario.json()["id"] == scenario.json()["id"]
    assert scenario.json()["scenario_projected_cost"] < scenario.json()["baseline_projected_cost"]
