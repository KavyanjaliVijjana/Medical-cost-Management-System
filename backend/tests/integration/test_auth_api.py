from fastapi.testclient import TestClient

from app.core.security import verify_password
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import app


def _registration_payload() -> dict[str, str]:
    return {
        "full_name": "Avery Morgan",
        "email": "avery.morgan@example.com",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
    }


def test_registers_a_user_with_a_hashed_password_and_no_password_response() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=_registration_payload())

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "avery.morgan@example.com"
    assert payload["display_name"] == "Avery Morgan"
    assert payload["is_demo"] is False
    assert "password" not in payload
    assert payload["access_token"]
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="avery.morgan@example.com").one()
        assert user.password_hash != "SecurePass123"
        assert verify_password("SecurePass123", user.password_hash)


def test_registration_rejects_duplicate_email_and_password_mismatch() -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/register", json=_registration_payload()).status_code == 201
        duplicate = client.post("/api/v1/auth/register", json=_registration_payload())
        mismatch = client.post(
            "/api/v1/auth/register",
            json={**_registration_payload(), "email": "other@example.com", "confirm_password": "Different123"},
        )

    assert duplicate.status_code == 409
    assert mismatch.status_code == 422


def test_normal_login_rejects_invalid_credentials_and_allows_seeded_demo_account() -> None:
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json=_registration_payload())
        login = client.post("/api/v1/auth/login", json={"email": "avery.morgan@example.com", "password": "SecurePass123"})
        invalid_login = client.post("/api/v1/auth/login", json={"email": "avery.morgan@example.com", "password": "wrong-password"})
        demo_login = client.post("/api/v1/auth/login", json={"email": "demo@medicalcost.local", "password": "Demo@12345"})

    assert login.status_code == 200
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "Invalid email or password."
    assert demo_login.status_code == 200
    assert demo_login.json()["is_demo"] is True


def test_profile_name_update_is_persisted() -> None:
    with TestClient(app) as client:
        registered = client.post("/api/v1/auth/register", json=_registration_payload()).json()
        response = client.patch(
            "/api/v1/auth/profile",
            json={"full_name": "Avery Chen"},
            headers={"Authorization": f"Bearer {registered['access_token']}"},
        )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Avery Chen"
    with SessionLocal() as db:
        assert db.get(User, registered["id"]).display_name == "Avery Chen"
