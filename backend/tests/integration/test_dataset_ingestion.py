import io

from fastapi.testclient import TestClient

from app.main import app


def test_validated_csv_is_stored_and_retrievable() -> None:
    csv_bytes = b"date,department,patient_count,total_cost\n2025-01-01,Cardiology,25,1200.50\n"
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/validate", files={"file": ("costs.csv", csv_bytes, "text/csv")})
        assert validation.status_code == 200
        payload = validation.json()
        assert payload["validation"]["is_valid"] is True
        assert payload["dataset"]["processing_status"] == "ready"

        dataset_id = payload["dataset"]["id"]
        processed = client.post(f"/api/v1/datasets/{dataset_id}/process")
        preview = client.get(f"/api/v1/datasets/{dataset_id}/preview")

    assert processed.status_code == 200
    assert processed.json()["processing_status"] == "completed"
    assert preview.status_code == 200
    assert preview.json()["records"][0]["department"] == "Cardiology"
    assert preview.json()["records"][0]["total_cost"] == 1200.5


def test_demo_dataset_can_be_validated_processed_and_retrieved() -> None:
    with TestClient(app) as client:
        validation = client.post("/api/v1/datasets/demo/validate")
        assert validation.status_code == 200
        payload = validation.json()
        assert payload["dataset"]["is_synthetic"] is True
        assert payload["dataset"]["name"] == "Synthetic Demo Dataset"
        assert payload["validation"]["valid_rows"] == 60

        dataset_id = payload["dataset"]["id"]
        processed = client.post(f"/api/v1/datasets/{dataset_id}/process")
        preview = client.get(f"/api/v1/datasets/{dataset_id}/preview")

    assert processed.status_code == 200
    assert len(preview.json()["records"]) == 10
