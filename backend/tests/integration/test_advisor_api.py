from fastapi.testclient import TestClient

from app.agent.advisor_agent import medical_economics_advisor
from app.main import app


def _prepared_dataset(client: TestClient, *, with_forecast: bool = True) -> int:
    validation = client.post("/api/v1/datasets/demo/validate")
    dataset_id = validation.json()["dataset"]["id"]
    client.post(f"/api/v1/datasets/{dataset_id}/process")
    if with_forecast:
        client.post("/api/v1/forecasts", json={"dataset_id": dataset_id, "horizon_months": 3})
        client.post(f"/api/v1/insights/datasets/{dataset_id}/drivers/generate")
        client.post(f"/api/v1/insights/datasets/{dataset_id}/alerts/generate")
        client.post(f"/api/v1/recommendations/datasets/{dataset_id}/generate")
    return dataset_id


def test_advisor_uses_real_evidence_for_required_questions_without_provider() -> None:
    expected_tools = {
        "Why are medical costs increasing?": ["analytics", "cost_pressures"],
        "What is the expected cost trend?": ["forecast"],
        "What are the biggest cost pressures?": ["cost_pressures"],
        "What should the medical economics team prioritize?": ["cost_pressures", "recommendations"],
        "What happens if Oncology costs are reduced by 5%?": ["scenario"],
    }
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        responses = {
            question: client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": question}).json()
            for question in expected_tools
        }

    for question, expected in expected_tools.items():
        payload = responses[question]
        assert payload["status"] == "provider_unavailable"
        assert payload["answer"] is None
        assert payload["tools_used"] == expected
        assert all(item["error"] is None for item in payload["evidence"])
    analytics = responses["Why are medical costs increasing?"]["evidence"][0]["result"]
    assert analytics["metrics"]["total_medical_cost"] > 0
    assert len(responses["What is the expected cost trend?"]["evidence"][0]["result"]["forecast_points"]) == 3
    scenario = responses["What happens if Oncology costs are reduced by 5%?"]["evidence"][0]["result"]
    assert scenario["scenario_projected_cost"] < scenario["baseline_projected_cost"]


def test_advisor_returns_missing_forecast_evidence_without_breaking() -> None:
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client, with_forecast=False)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "What is the expected cost trend?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "provider_unavailable"
    assert payload["evidence"][0]["tool"] == "forecast"
    assert "No persisted forecast" in payload["evidence"][0]["error"]


def test_advisor_rejects_invalid_scenario_reduction() -> None:
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "What happens if Oncology costs are reduced by 200%?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["tools_used"] == ["scenario"]
    assert "no more than 100" in payload["evidence"][0]["error"]


def test_advisor_provider_failure_preserves_deterministic_evidence(monkeypatch) -> None:
    class FailingProvider:
        name = "openai"
        model = "test-model"

        def available(self) -> bool:
            return True

        def generate(self, *, instructions: str, input_text: str) -> str:
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(medical_economics_advisor, "llm_provider", FailingProvider())
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "Why are medical costs increasing?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "provider_error"
    assert payload["answer"] is None
    assert payload["evidence"][0]["result"]["metrics"]["total_medical_cost"] > 0
