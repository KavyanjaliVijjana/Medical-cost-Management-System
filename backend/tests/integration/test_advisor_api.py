from pathlib import Path

from fastapi.testclient import TestClient

from app.agent.advisor_agent import medical_economics_advisor
from app.agent.specialists import COST_PRESSURE_ACTION_SPECIALIST, SCENARIO_SPECIALIST, SUPERVISOR_NAME, TREND_FORECAST_SPECIALIST
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
    expected_routes = {
        "Why are medical costs increasing?": (["analytics", "cost_pressures"], [TREND_FORECAST_SPECIALIST, COST_PRESSURE_ACTION_SPECIALIST]),
        "Why did our medical expenses increase?": (["analytics", "cost_pressures"], [TREND_FORECAST_SPECIALIST, COST_PRESSURE_ACTION_SPECIALIST]),
        "What is the expected cost trend?": (["forecast"], [TREND_FORECAST_SPECIALIST]),
        "Are costs expected to rise over the next few months?": (["forecast"], [TREND_FORECAST_SPECIALIST]),
        "What are the biggest cost pressures?": (["cost_pressures"], [COST_PRESSURE_ACTION_SPECIALIST]),
        "Which areas are putting the most pressure on costs?": (["cost_pressures"], [COST_PRESSURE_ACTION_SPECIALIST]),
        "What should leadership focus on?": (["cost_pressures", "recommendations"], [COST_PRESSURE_ACTION_SPECIALIST]),
        "What happens if Oncology costs are reduced by 10%?": (["scenario"], [SCENARIO_SPECIALIST]),
        "Give me an executive summary of this dataset.": (["analytics", "forecast", "cost_pressures", "recommendations"], [TREND_FORECAST_SPECIALIST, COST_PRESSURE_ACTION_SPECIALIST]),
    }
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        responses = {
            question: client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": question}).json()
            for question in expected_routes
        }

    for question, (expected_tools, expected_specialists) in expected_routes.items():
        payload = responses[question]
        assert payload["status"] == "provider_unavailable"
        assert payload["answer"]
        assert payload["supervisor"] == SUPERVISOR_NAME
        assert payload["specialists_invoked"] == expected_specialists
        assert payload["tools_used"] == expected_tools
        assert all(item["error"] is None for item in payload["evidence"])
    analytics = responses["Why are medical costs increasing?"]["evidence"][0]["result"]
    assert analytics["metrics"]["total_medical_cost"] > 0
    assert len(responses["What is the expected cost trend?"]["evidence"][0]["result"]["forecast_points"]) == 3
    scenario = responses["What happens if Oncology costs are reduced by 10%?"]["evidence"][0]["result"]
    assert scenario["scenario_projected_cost"] < scenario["baseline_projected_cost"]
    assert "SUMMARY" in responses["Why are medical costs increasing?"]["answer"]
    assert "KEY EVIDENCE" in responses["What are the biggest cost pressures?"]["answer"]
    assert "FORECAST" in responses["Are costs expected to rise over the next few months?"]["answer"]
    assert "RECOMMENDED FOCUS" in responses["What should leadership focus on?"]["answer"]
    assert "HYPOTHETICAL SCENARIO" in responses["What happens if Oncology costs are reduced by 10%?"]["answer"]


def test_advisor_returns_missing_forecast_evidence_without_breaking() -> None:
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client, with_forecast=False)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "What is the expected cost trend?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "provider_unavailable"
    assert "SUMMARY" in payload["answer"]
    assert payload["specialists_invoked"] == [TREND_FORECAST_SPECIALIST]
    assert payload["evidence"][0]["tool"] == "forecast"
    assert "No persisted forecast" in payload["evidence"][0]["error"]
    assert "No complete evidence" in payload["answer"]


def test_advisor_keeps_available_executive_evidence_when_forecast_is_missing() -> None:
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client, with_forecast=False)
        response = client.post(
            "/api/v1/advisor/ask",
            json={"dataset_id": dataset_id, "question": "Give me an executive summary of this dataset."},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "provider_unavailable"
    assert "SOURCE" in payload["answer"]
    assert payload["specialists_invoked"] == [TREND_FORECAST_SPECIALIST, COST_PRESSURE_ACTION_SPECIALIST]
    evidence = {item["tool"]: item for item in payload["evidence"]}
    assert evidence["analytics"]["result"]["metrics"]["total_medical_cost"] > 0
    assert "No persisted forecast" in evidence["forecast"]["error"]
    assert evidence["cost_pressures"]["error"] is None
    assert evidence["recommendations"]["error"] is None


def test_advisor_rejects_unrelated_questions_without_calling_tools() -> None:
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "What is the weather today?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "unsupported_question"
    assert payload["specialists_invoked"] == []
    assert payload["tools_used"] == []
    assert payload["evidence"] == []
    assert "medical cost trends" in payload["message"]


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

        def __init__(self) -> None:
            self.calls = 0

        def available(self) -> bool:
            return True

        def generate(self, *, instructions: str, input_text: str) -> str:
            self.calls += 1
            raise RuntimeError("provider unavailable")

    provider = FailingProvider()
    monkeypatch.setattr(medical_economics_advisor, "llm_provider", provider)
    with TestClient(app) as client:
        dataset_id = _prepared_dataset(client)
        response = client.post("/api/v1/advisor/ask", json={"dataset_id": dataset_id, "question": "Why are medical costs increasing?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "provider_error"
    assert payload["answer"]
    assert payload["evidence"][0]["result"]["metrics"]["total_medical_cost"] > 0
    assert provider.calls == 1


def test_agent_package_has_no_direct_database_or_repository_imports() -> None:
    agent_directory = Path(__file__).resolve().parents[2] / "app" / "agent"
    forbidden_imports = ("sqlalchemy", "app.db.models", "app.repositories")
    for source_file in agent_directory.glob("*.py"):
        source = source_file.read_text(encoding="utf-8")
        assert not any(forbidden in source for forbidden in forbidden_imports), source_file.name
