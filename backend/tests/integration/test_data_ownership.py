from fastapi.testclient import TestClient

from app.main import app


def _register(client: TestClient, label: str) -> tuple[dict, dict[str, str]]:
    payload = {
        "full_name": f"Owner {label}",
        "email": f"owner.{label.lower()}@example.com",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user = response.json()
    return user, {"Authorization": f"Bearer {user['access_token']}"}


def test_dataset_and_downstream_results_are_isolated_by_authenticated_owner() -> None:
    with TestClient(app) as client:
        _, user_a_headers = _register(client, "A")
        _, user_b_headers = _register(client, "B")

        assert client.get("/api/v1/datasets", headers=user_a_headers).json() == []
        assert client.get("/api/v1/datasets", headers=user_b_headers).json() == []

        validated = client.post("/api/v1/datasets/demo/validate", headers=user_a_headers)
        assert validated.status_code == 200
        dataset_id = validated.json()["dataset"]["id"]
        assert client.post(f"/api/v1/datasets/{dataset_id}/process", headers=user_a_headers).status_code == 200
        assert [item["id"] for item in client.get("/api/v1/datasets", headers=user_a_headers).json()] == [dataset_id]

        analytics = client.get(f"/api/v1/analytics/datasets/{dataset_id}/summary", headers=user_a_headers)
        assert analytics.status_code == 200
        forecast = client.post("/api/v1/forecasts", json={"dataset_id": dataset_id, "horizon_months": 3}, headers=user_a_headers)
        assert forecast.status_code == 200
        forecast_id = forecast.json()["id"]
        assert client.post(f"/api/v1/insights/datasets/{dataset_id}/drivers/generate", headers=user_a_headers).status_code == 200
        assert client.post(f"/api/v1/insights/datasets/{dataset_id}/alerts/generate", headers=user_a_headers).status_code == 200
        assert client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate", headers=user_a_headers).status_code == 200
        scenario = client.post("/api/v1/scenarios", json={"dataset_id": dataset_id, "department": "Oncology", "reduction_pct": 10}, headers=user_a_headers)
        assert scenario.status_code == 200
        scenario_id = scenario.json()["id"]

        forbidden = [
            ("get", f"/api/v1/datasets/{dataset_id}"),
            ("get", f"/api/v1/datasets/{dataset_id}/preview"),
            ("get", f"/api/v1/analytics/datasets/{dataset_id}/summary"),
            ("get", f"/api/v1/forecasts/datasets/{dataset_id}/latest"),
            ("get", f"/api/v1/forecasts/{forecast_id}"),
            ("get", f"/api/v1/insights/datasets/{dataset_id}/drivers"),
            ("get", f"/api/v1/insights/datasets/{dataset_id}/alerts"),
            ("get", f"/api/v1/recommendations/datasets/{dataset_id}"),
            ("get", f"/api/v1/scenarios/datasets/{dataset_id}/latest"),
            ("get", f"/api/v1/scenarios/{scenario_id}"),
        ]
        for method, path in forbidden:
            response = getattr(client, method)(path, headers=user_b_headers)
            assert response.status_code == 404
        advisor = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "Why are medical costs increasing?"}, headers=user_b_headers)
        assert advisor.status_code == 404
        assert client.get("/api/v1/datasets", headers=user_b_headers).json() == []

        user_b_demo = client.post("/api/v1/datasets/demo/validate", headers=user_b_headers)
        user_b_dataset_id = user_b_demo.json()["dataset"]["id"]
        assert client.post(f"/api/v1/datasets/{user_b_dataset_id}/process", headers=user_b_headers).status_code == 200
        assert [item["id"] for item in client.get("/api/v1/datasets", headers=user_b_headers).json()] == [user_b_dataset_id]
        assert [item["id"] for item in client.get("/api/v1/datasets", headers=user_a_headers).json()] == [dataset_id]
