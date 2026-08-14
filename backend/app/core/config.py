from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_name: str = "Medical Cost Management"
    app_env: str = "development"
    database_url: str = "sqlite:///./medical_cost.db"
    cors_origins: str = "http://localhost:5173"
    alert_mom_cost_threshold_pct: float = 5.0
    alert_cost_per_patient_threshold_pct: float = 5.0
    alert_department_concentration_threshold_pct: float = 30.0
    advisor_llm_provider: str = "disabled"
    advisor_llm_api_key: str | None = None
    advisor_llm_model: str = "gpt-5-mini"
    advisor_llm_base_url: str = "https://api.openai.com/v1"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
