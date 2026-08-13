from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_database_connection() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"


def test_seeded_demo_user_can_log_in() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/demo-login", json={"email": "demo@medicalcost.local"})

    assert response.status_code == 200
    assert response.json()["is_demo"] is True
