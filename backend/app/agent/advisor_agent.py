from __future__ import annotations

import json

from app.agent.advisor_tools import AdvisorToolExecutor, ToolEvidence
from app.agent.llm_provider import AdvisorLLMProvider, create_llm_provider
from app.agent.specialists import (
    COST_PRESSURE_ACTION_SPECIALIST,
    SCENARIO_SPECIALIST,
    SUPERVISOR_NAME,
    TREND_FORECAST_SPECIALIST,
    CostPressureActionSpecialist,
    ScenarioSpecialist,
    SpecialistResult,
    SpecialistTask,
    TrendForecastSpecialist,
)
from app.core.config import get_settings
from app.schemas.advisor import AdvisorResponse


SYSTEM_INSTRUCTIONS = """You are the Medical Economics Advisor for a healthcare-finance application.
Use only the structured evidence supplied in the input. Do not invent values, forecasts, savings,
alerts, recommendations, or causal claims. This is not clinical decision support: never diagnose,
recommend treatment, prescribe, or discuss patient-level information.

Return a concise dashboard-ready response with three to six short sections when evidence permits:
SUMMARY, WHAT THE DATA SHOWS, WHY IT MATTERS, RECOMMENDED FOCUS, and EVIDENCE. Give every number
plain-language context. Explicitly label observed historical values as ACTUAL, model values as FORECAST,
and scenario values as HYPOTHETICAL. Forecasts are planning estimates, not observed spending. Scenarios
are hypothetical estimates, not guaranteed savings. If the data shows movement but does not establish why,
say that it does not establish a specific causal factor. Include a recommended action only when it comes
from supplied driver, alert, or recommendation evidence. Do not present raw JSON or internal tool details
as the primary answer. If a required tool is unavailable, state what is unavailable and retain other valid
evidence."""

CLINICAL_TERMS = ("diagnos", "diagnosis", "prescrib", "treatment", "medication", "patient care", "clinical")
BUSINESS_TERMS = ("cost", "expense", "spend", "medical", "utilization", "patient", "forecast", "trend", "pressure", "driver", "department", "recommend", "priorit", "leadership", "scenario", "projected", "summary", "oncology", "pharmacy", "site of care", "service mix", "unit cost")
UNSUPPORTED_QUESTION_MESSAGE = "I can help analyze medical cost trends, forecast cost pressure, identify cost drivers, evaluate cost-containment recommendations, and run what-if scenarios for the selected dataset."


class MedicalEconomicsSupervisorAgent:
    """Routes questions to thin specialists and optionally synthesizes their deterministic evidence."""

    def __init__(self, *, llm_provider: AdvisorLLMProvider | None = None) -> None:
        self.llm_provider = llm_provider or create_llm_provider(get_settings())
        self._specialists = {
            TREND_FORECAST_SPECIALIST: TrendForecastSpecialist(),
            COST_PRESSURE_ACTION_SPECIALIST: CostPressureActionSpecialist(),
            SCENARIO_SPECIALIST: ScenarioSpecialist(),
        }

    def answer(self, *, executor: AdvisorToolExecutor, dataset_id: int, question: str) -> AdvisorResponse:
        normalized_question = question.lower()
        if any(term in normalized_question for term in CLINICAL_TERMS):
            return self._unsupported(dataset_id, question, f"The advisor does not provide clinical guidance. {UNSUPPORTED_QUESTION_MESSAGE}")
        if not any(term in normalized_question for term in BUSINESS_TERMS):
            return self._unsupported(dataset_id, question, UNSUPPORTED_QUESTION_MESSAGE)

        tasks = self.select_specialists(question)
        specialist_results = [self._specialists[task.specialist].analyze(executor, dataset_id=dataset_id, question=question, tools=task.tools) for task in tasks]
        evidence = [item for result in specialist_results for item in result.evidence]
        response = AdvisorResponse(
            dataset_id=dataset_id,
            question=question,
            status="provider_unavailable",
            answer=_deterministic_answer(evidence),
            message="Deterministic evidence response. Configure an optional LLM provider for additional synthesis.",
            supervisor=SUPERVISOR_NAME,
            specialists_invoked=[result.specialist for result in specialist_results],
            tools_used=[item.tool for item in evidence],
            evidence=evidence,
            provider=self.llm_provider.name,
            model=self.llm_provider.model,
        )
        if not self.llm_provider.available():
            return response
        try:
            response.answer = self.llm_provider.generate(
                instructions=SYSTEM_INSTRUCTIONS,
                input_text=json.dumps({"question": question, "dataset_id": dataset_id, "supervisor": SUPERVISOR_NAME, "specialists": [_specialist_dump(result) for result in specialist_results], "tool_evidence": [_evidence_dump(item) for item in evidence]}, default=str),
            )
            response.status = "completed"
            response.message = None
        except RuntimeError:
            response.status = "provider_error"
            response.answer = _deterministic_answer(evidence)
            response.message = "The configured LLM provider could not produce a response; this deterministic evidence response is shown instead."
        return response

    def _unsupported(self, dataset_id: int, question: str, message: str) -> AdvisorResponse:
        return AdvisorResponse(dataset_id=dataset_id, question=question, status="unsupported_question", answer=None, message=message, supervisor=SUPERVISOR_NAME, specialists_invoked=[], tools_used=[], evidence=[], provider=self.llm_provider.name, model=self.llm_provider.model)

    @staticmethod
    def select_specialists(question: str) -> list[SpecialistTask]:
        normalized = question.lower()
        if any(phrase in normalized for phrase in ("what happens if", "what if", "reduced by", "reduction", "falls by", "fall by", "decreased by", "decrease by", "drops by", "drop by")):
            return [SpecialistTask(SCENARIO_SPECIALIST, ("scenario",))]
        if any(phrase in normalized for phrase in ("biggest cost pressures", "most pressure", "most cost pressure")):
            return [SpecialistTask(COST_PRESSURE_ACTION_SPECIALIST, ("cost_pressures",))]
        if any(phrase in normalized for phrase in ("executive summary", "summarize this dataset", "summary of this dataset")):
            return [SpecialistTask(TREND_FORECAST_SPECIALIST, ("analytics", "forecast")), SpecialistTask(COST_PRESSURE_ACTION_SPECIALIST, ("cost_pressures", "recommendations"))]
        if any(phrase in normalized for phrase in ("prioritize", "priority", "what should", "leadership focus", "should leadership")):
            return [SpecialistTask(COST_PRESSURE_ACTION_SPECIALIST, ("cost_pressures", "recommendations"))]
        if any(phrase in normalized for phrase in ("cost pressure", "pressure", "why are", "why is", "why did")):
            return [SpecialistTask(TREND_FORECAST_SPECIALIST, ("analytics",)), SpecialistTask(COST_PRESSURE_ACTION_SPECIALIST, ("cost_pressures",))]
        if any(phrase in normalized for phrase in ("expected cost trend", "expected costs", "forecast", "expected trend", "cost trend", "expected to rise", "expected to fall", "next few months")):
            return [SpecialistTask(TREND_FORECAST_SPECIALIST, ("forecast",))]
        return [SpecialistTask(TREND_FORECAST_SPECIALIST, ("analytics",))]


MedicalEconomicsAdvisorAgent = MedicalEconomicsSupervisorAgent


def _evidence_dump(evidence: ToolEvidence) -> dict[str, object]:
    return {"tool": evidence.tool, "result": evidence.result, "error": evidence.error}


def _specialist_dump(result: SpecialistResult) -> dict[str, object]:
    return {"specialist": result.specialist, "evidence": [_evidence_dump(item) for item in result.evidence]}


medical_economics_advisor = MedicalEconomicsSupervisorAgent()


def _deterministic_answer(evidence: list[ToolEvidence]) -> str:
    """Present existing specialist evidence as a concise, decision-oriented dashboard narrative."""
    results = {item.tool: item.result or {} for item in evidence if item.error is None}
    analytics = results.get("analytics", {})
    forecast = results.get("forecast", {})
    pressures = results.get("cost_pressures", {})
    recommendations = results.get("recommendations", {})
    scenario = results.get("scenario", {})
    if scenario:
        return _scenario_answer(scenario)

    metrics = _mapping(analytics.get("metrics"))
    highest = _mapping(analytics.get("highest_cost_department"))
    drivers = _items(pressures.get("drivers"))
    alerts = _items(pressures.get("alerts"))
    recommendations_list = _items(recommendations.get("recommendations"))
    change = metrics.get("month_over_month_cost_change_pct")
    lines: list[str] = ["SUMMARY", _summary(change, forecast, drivers, alerts), "", "WHAT THE DATA SHOWS"]

    if isinstance(metrics.get("total_medical_cost"), (int, float)):
        total_cost = _currency(metrics["total_medical_cost"])
        patients = metrics.get("total_patient_count")
        patient_context = f" across {patients:,} recorded patients" if isinstance(patients, int) else ""
        lines.append(f"- ACTUAL: The analyzed dataset contains {total_cost} in total historical medical costs{patient_context}.")
    if isinstance(metrics.get("cost_per_patient"), (int, float)):
        lines.append(f"- ACTUAL: Historical cost per patient is {_currency(metrics['cost_per_patient'])}.")
    if isinstance(change, (int, float)):
        latest_month = metrics.get("latest_month")
        latest_cost = metrics.get("latest_month_cost")
        month_context = f" in {latest_month}" if latest_month else ""
        amount_context = f" to {_currency(latest_cost)}" if isinstance(latest_cost, (int, float)) else ""
        lines.append(f"- ACTUAL: Latest monthly cost changed {_percent(change)}{amount_context}{month_context} versus the previous month.")
    if highest and highest.get("department"):
        contribution = highest.get("contribution_pct")
        share = f", representing {_percentage(contribution)} of total medical cost" if isinstance(contribution, (int, float)) else ""
        lines.append(f"- ACTUAL: {highest['department']} is the highest-cost department{share}.")
    _append_forecast_evidence(lines, forecast)
    for item in drivers[:2]:
        if item.get("explanation"):
            lines.append(f"- ACTUAL DRIVER: {item['explanation']}")
    for item in alerts[:1]:
        if item.get("explanation"):
            lines.append(f"- ACTUAL ALERT: {item['explanation']}")
    if len(lines) == 4:
        lines.append("- No complete deterministic evidence is currently available for the selected dataset.")

    lines.extend(["", "WHY IT MATTERS"])
    if forecast and not analytics and not pressures:
        lines.append("FORECAST values are planning estimates rather than observed spending and can help the team prepare for potential future cost pressure.")
    elif isinstance(change, (int, float)):
        lines.append("The available data shows month-to-month movement, but it does not establish a specific causal factor.")
    elif drivers or alerts:
        lines.append("The observed drivers and alerts identify where operational review is warranted, but they do not establish a specific causal factor.")
    else:
        lines.append("Additional completed historical data or stored results are needed before a business conclusion can be drawn.")

    if recommendations_list:
        recommendation = recommendations_list[0]
        if recommendation.get("title") or recommendation.get("rationale"):
            lines.extend(["", "RECOMMENDED FOCUS"])
            priority = f" ({recommendation['priority']} priority)" if recommendation.get("priority") else ""
            lines.append(f"{recommendation.get('title', 'Evidence-based recommendation')}{priority}: {recommendation.get('rationale', 'Review the supporting evidence before taking action.')}")
            supporting_evidence = recommendation.get("supporting_evidence")
            if isinstance(supporting_evidence, list) and supporting_evidence:
                lines.append(f"Evidence: {supporting_evidence[0]}")
    elif highest or drivers or alerts:
        lines.extend(["", "NEXT REVIEW"])
        lines.append("Review the highest-pressure department and its associated driver or alert evidence in the Insights workspace before taking action.")

    _append_availability(lines, evidence)
    _append_source(lines, analytics, forecast)
    return "\n".join(lines)


def _scenario_answer(scenario: dict[str, object]) -> str:
    department = scenario.get("department", "the selected department")
    reduction_pct = scenario.get("reduction_pct")
    share = scenario.get("department_cost_share_pct")
    share_context = f" Its historical cost share is {_percentage(share)}." if isinstance(share, (int, float)) else ""
    reduction_context = f" by {_percentage(reduction_pct)}" if isinstance(reduction_pct, (int, float)) else ""
    return "\n".join(
        [
            "HYPOTHETICAL SCENARIO",
            f"This is a hypothetical estimate, not an observed result or guaranteed savings. The scenario models reducing {department}{reduction_context}.{share_context}",
            "",
            "WHAT THE SCENARIO SHOWS",
            f"- HYPOTHETICAL: Baseline projected cost is {_currency(scenario.get('baseline_projected_cost'))}.",
            f"- HYPOTHETICAL: Estimated reduction is {_currency(scenario.get('estimated_reduction_amount'))}.",
            f"- HYPOTHETICAL: Scenario projected cost is {_currency(scenario.get('scenario_projected_cost'))}.",
            "",
            "WHY IT MATTERS",
            "Use this estimate to assess the potential financial impact of a cost-containment decision before implementation; it does not predict guaranteed savings.",
            "",
            "EVIDENCE",
            "The estimate uses the latest stored forecast and the selected department's historical cost share.",
        ]
    )


def _summary(change: object, forecast: dict[str, object], drivers: list[dict[str, object]], alerts: list[dict[str, object]]) -> str:
    if isinstance(change, (int, float)):
        direction = "upward" if change > 0 else "downward" if change < 0 else "stable"
        return f"Medical costs show {direction} month-to-month movement ({_percent(change)} versus the previous month)."
    if forecast:
        horizon = forecast.get("horizon_months")
        return f"A {horizon}-month stored cost forecast is available for planning." if horizon else "A stored cost forecast is available for planning."
    if drivers or alerts:
        return "Existing driver and alert evidence identifies the current areas of medical-cost pressure."
    return "The requested evidence is not currently available for the selected dataset."


def _append_forecast_evidence(lines: list[str], forecast: dict[str, object]) -> None:
    if not forecast:
        return
    model_name = forecast.get("model_name", "stored model")
    horizon = forecast.get("horizon_months")
    lines.append(f"- FORECAST: The {model_name} provides a {horizon}-month outlook." if horizon else f"- FORECAST: A stored outlook is available from {model_name}.")
    for point in _items(forecast.get("forecast_points"))[:12]:
        month = point.get("forecast_month") or point.get("month") or "Forecast period"
        lines.append(f"  - FORECAST: {str(month)[:7]} projected medical cost: {_currency(point.get('predicted_cost'))}.")
    expected = forecast.get("expected_change_pct")
    if isinstance(expected, (int, float)):
        lines.append(f"- FORECAST: The final projected month is {_percent(expected)} versus the latest observed monthly cost.")


def _append_availability(lines: list[str], evidence: list[ToolEvidence]) -> None:
    unavailable = [f"{item.tool.replace('_', ' ')}: {item.error}" for item in evidence if item.error]
    if unavailable:
        lines.extend(["", "DATA AVAILABILITY"])
        lines.extend(f"- {item}" for item in unavailable)


def _append_source(lines: list[str], analytics: dict[str, object], forecast: dict[str, object]) -> None:
    dataset = _mapping(analytics.get("dataset")) or _mapping(forecast.get("dataset"))
    trend = _items(analytics.get("monthly_trend")) or _items(forecast.get("historical_monthly_cost"))
    if not dataset and not trend:
        return
    lines.extend(["", "SOURCE"])
    if dataset:
        label = "Synthetic demo data — not real medical data" if dataset.get("is_synthetic") else "Uploaded aggregated medical-cost data"
        lines.append(f"{dataset.get('name', 'Selected dataset')} · {label}")
    months = [item.get("month") for item in trend if item.get("month")]
    if months:
        lines.append(f"Historical period: {str(months[0])[:7]} to {str(months[-1])[:7]}")


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _items(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _currency(value: object) -> str:
    return f"${value:,.0f}" if isinstance(value, (int, float)) else "Not available"


def _percent(value: float) -> str:
    return f"{value:+.1f}%"


def _percentage(value: float) -> str:
    return f"{value:.1f}%"
