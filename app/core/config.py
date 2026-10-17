from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    google_api_key: str = Field(..., description="Gemini API key")
    gemini_model: str = "gemini-3.5-flash-lite"

    # Database
    database_url: str = ""

    # App behavior
    log_level: str = "INFO"
    max_revisions: int = Field(default=3, ge=1, le=10)

        # Guardrails: input size limits
    min_jd_chars: int = 100
    max_jd_chars: int = 10000
    min_cv_chars: int = 100
    max_cv_chars: int = 20000

    # Guardrails: rate limit for POST /applications (per client IP)
    rate_limit_max_requests: int = 5
    rate_limit_window_seconds: int = 600

    # Observability
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""

    langsmith_project: str = "job-application-assistant"
    langsmith_endpoint: str = ""  # only needed for EU accounts

    # Security: if set, /applications endpoints require this in the X-API-Key header
    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Create the Settings object once and reuse it everywhere."""
    return Settings()