from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "AI Incident Copilot"
    aic_model: str = "mistral-3.5"
    aic_allowed_models: str = "mistral-3.5"
    aic_max_iterations: int = Field(default=20, ge=1, le=20)
    aic_log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://aic:aic@postgres:5432/aic"
    qdrant_url: str = "http://qdrant:6333"
    mem0_collection: str = "aic_incident_memory"
    mem0_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    mem0_embedding_dims: int = Field(default=384, ge=1)
    mem0_min_score: float = Field(default=0.45, ge=0, le=1)
    mem0_user_id: str = "aic-demo"
    mem0_agent_id: str = "holmes-k8s-poc"
    mem0_telemetry: bool = False

    holmes_url: str = "http://holmesgpt:5050"
    holmes_api_key: SecretStr = SecretStr("")
    holmes_timeout_seconds: float = Field(default=300.0, ge=1, le=600)
    holmes_max_response_bytes: int = Field(default=1_048_576, ge=1024, le=1_048_576)
    holmes_approval_ttl_seconds: int = Field(default=900, ge=60, le=3600)

    litellm_base_url: str = "https://llmpipe.vnpost.vn/v1"
    litellm_api_key: SecretStr = SecretStr("")

    @property
    def allowed_models(self) -> frozenset[str]:
        return frozenset(item.strip() for item in self.aic_allowed_models.split(",") if item.strip())

    @field_validator("aic_log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("AIC_LOG_LEVEL is invalid")
        return normalized

    @model_validator(mode="after")
    def validate_model_and_urls(self) -> "Settings":
        if self.aic_model not in self.allowed_models:
            raise ValueError("AIC_MODEL must be included in AIC_ALLOWED_MODELS")
        for name, value in (("QDRANT_URL", self.qdrant_url), ("HOLMES_URL", self.holmes_url)):
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError(f"{name} must be an http(s) URL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
