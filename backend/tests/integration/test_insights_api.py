from fastapi.testclient import TestClient

from app.main import app


def test_driver_and_alert_generation_returns_evidence_backed_results() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        drivers = client.post(f"/api/v1/insights/datasets/{dataset_id}/drivers/generate")
        alerts = client.post(f"/api/v1/insights/datasets/{dataset_id}/alerts/generate")
        retrieved_drivers = client.get(f"/api/v1/insights/datasets/{dataset_id}/drivers")
        retrieved_alerts = client.get(f"/api/v1/insights/datasets/{dataset_id}/alerts")

    assert drivers.status_code == 200
    assert len(drivers.json()) == 4
    assert drivers.json()[0]["baseline_value"] is not None
    assert drivers.json()[0]["explanation"]
    assert alerts.status_code == 200
    assert any(alert["metric"] == "Department cost concentration" for alert in alerts.json())
    assert retrieved_drivers.json() == drivers.json()
    assert retrieved_alerts.json() == alerts.json()
