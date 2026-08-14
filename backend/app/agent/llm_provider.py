from __future__ import annotations

from typing import Protocol

import httpx

from app.core.config import Settings


class AdvisorLLMProvider(Protocol):
    name: str
    model: str | None

    def available(self) -> bool: ...

    def generate(self, *, instructions: str, input_text: str) -> str: ...


class UnavailableProvider:
    name = "disabled"
    model = None

    def available(self) -> bool:
        return False

    def generate(self, *, instructions: str, input_text: str) -> str:
        raise RuntimeError("No LLM provider is configured.")


class OpenAIResponsesProvider:
    """Small optional adapter for the OpenAI Responses API; no application data is persisted here."""

    name = "openai"

    def __init__(self, *, api_key: str | None, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def available(self) -> bool:
        return bool(self.api_key and self.model)

    def generate(self, *, instructions: str, input_text: str) -> str:
        if not self.available():
            raise RuntimeError("OpenAI provider credentials are not configured.")
        try:
            response = httpx.post(
                f"{self.base_url}/responses",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "instructions": instructions, "input": input_text, "store": False},
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise RuntimeError("The configured OpenAI provider could not complete the advisor response.") from error
        payload = response.json()
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        raise RuntimeError("The configured OpenAI provider returned no text response.")


def create_llm_provider(settings: Settings) -> AdvisorLLMProvider:
    if settings.advisor_llm_provider.lower() == "openai":
        return OpenAIResponsesProvider(
            api_key=settings.advisor_llm_api_key,
            model=settings.advisor_llm_model,
            base_url=settings.advisor_llm_base_url,
        )
    return UnavailableProvider()
