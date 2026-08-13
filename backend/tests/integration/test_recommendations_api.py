from fastapi.testclient import TestClient

from app.main import app


def test_recommendations_are_evidence_backed_and_replace_prior_generation() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        client.post(f"/api/v1/insights/datasets/{dataset_id}/drivers/generate")
        client.post(f"/api/v1/insights/datasets/{dataset_id}/alerts/generate")
        first = client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate")
        second = client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate")
        retrieved = client.get(f"/api/v1/recommendations/datasets/{dataset_id}")

    assert first.status_code == 200
    assert len(first.json()) == 1
    assert first.json()[0]["triggering_metric"] == "Department cost concentration"
    assert first.json()[0]["supporting_evidence"]
    assert len(second.json()) == 1
    assert retrieved.json() == second.json()


def test_unsupported_recommendations_are_not_generated_without_evidence() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        dataset_id = validation.json()["dataset"]["id"]
        client.post(f"/api/v1/datasets/{dataset_id}/process")
        response = client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate")

    assert response.status_code == 200
    assert response.json() == []
