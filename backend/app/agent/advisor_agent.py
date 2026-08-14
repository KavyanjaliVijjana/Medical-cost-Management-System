from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.agent.advisor_tools import MedicalEconomicsTools, ToolEvidence
from app.agent.llm_provider import AdvisorLLMProvider, create_llm_provider
from app.core.config import get_settings
from app.schemas.advisor import AdvisorResponse


SYSTEM_INSTRUCTIONS = """You are the Medical Economics Advisor for a healthcare-finance application.
Use only the structured evidence supplied in the input. Do not invent values, forecasts, savings,
alerts, recommendations, or causal claims. This is not clinical decision support: never diagnose,
recommend treatment, prescribe, or discuss patient-level information. Be concise and business-oriented.
When useful, use headings: Finding, Evidence, Why it matters, Recommended action, Scenario impact.
Explicitly label observed facts as ACTUAL, model outputs as FORECAST, and scenario output as HYPOTHETICAL.
Never describe a scenario estimate as guaranteed savings. If a tool reports unavailable data, state that clearly."""

CLINICAL_TERMS = ("diagnos", "diagnosis", "prescrib", "treatment", "medication", "patient care", "clinical")


class MedicalEconomicsAdvisorAgent:
    """Question router and LLM synthesis coordinator; all data access remains in controlled tools."""

    def __init__(self, *, tools: MedicalEconomicsTools | None = None, llm_provider: AdvisorLLMProvider | None = None) -> None:
        self.tools = tools or MedicalEconomicsTools()
        self.llm_provider = llm_provider or create_llm_provider(get_settings())

    def answer(self, db: Session, *, dataset_id: int, question: str) -> AdvisorResponse:
        if any(term in question.lower() for term in CLINICAL_TERMS):
            return AdvisorResponse(
                dataset_id=dataset_id,
                question=question,
                status="unsupported_question",
                answer=None,
                message="The advisor supports healthcare-finance and operational cost questions only; it does not provide clinical guidance.",
                tools_used=[],
                evidence=[],
                provider=self.llm_provider.name,
                model=self.llm_provider.model,
            )

        selected_tools = self.select_tools(question)
        evidence = [self.tools.execute(tool, db=db, dataset_id=dataset_id, question=question) for tool in selected_tools]
        response = AdvisorResponse(
            dataset_id=dataset_id,
            question=question,
            status="provider_unavailable",
            answer=None,
            message="The advisor retrieved deterministic evidence, but no LLM provider is configured. Configure ADVISOR_LLM_PROVIDER, ADVISOR_LLM_API_KEY, and ADVISOR_LLM_MODEL to synthesize an AI response.",
            tools_used=selected_tools,
            evidence=evidence,
            provider=self.llm_provider.name,
            model=self.llm_provider.model,
        )
        if not self.llm_provider.available():
            return response
        try:
            response.answer = self.llm_provider.generate(
                instructions=SYSTEM_INSTRUCTIONS,
                input_text=json.dumps({"question": question, "dataset_id": dataset_id, "tool_evidence": [_evidence_dump(item) for item in evidence]}, default=str),
            )
            response.status = "completed"
            response.message = None
        except RuntimeError:
            response.status = "provider_error"
            response.message = "The advisor retrieved deterministic evidence, but the configured LLM provider could not produce a response."
        return response

    @staticmethod
    def select_tools(question: str) -> list[str]:
        normalized = question.lower()
        if any(phrase in normalized for phrase in ("what happens if", "what if", "reduced by", "reduction")):
            return ["scenario"]
        if "biggest cost pressures" in normalized:
            return ["cost_pressures"]
        if any(phrase in normalized for phrase in ("executive summary", "summarize this dataset", "summary of this dataset")):
            return ["analytics", "forecast", "cost_pressures", "recommendations"]
        if any(phrase in normalized for phrase in ("prioritize", "priority", "what should")):
            return ["cost_pressures", "recommendations"]
        if any(phrase in normalized for phrase in ("cost pressure", "pressure", "why are", "why is")):
            return ["analytics", "cost_pressures"]
        if any(phrase in normalized for phrase in ("expected cost trend", "forecast", "expected trend", "cost trend")):
            return ["forecast"]
        return ["analytics"]


def _evidence_dump(evidence: ToolEvidence) -> dict[str, object]:
    return {"tool": evidence.tool, "result": evidence.result, "error": evidence.error}


medical_economics_advisor = MedicalEconomicsAdvisorAgent()
