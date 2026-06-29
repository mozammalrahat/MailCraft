"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StrategyConfiguration(BaseModel):
    """Model and name pairing for a prompting strategy."""

    name: str
    model: str


class Settings(BaseSettings):
    """Runtime settings for MailCraft."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "MailCraft"
    debug: bool = False
    google_api_key: str = ""

    google_model_a: str = Field(validation_alias="GOOGLE_MODEL_A")
    google_model_b: str = Field(validation_alias="GOOGLE_MODEL_B")
    google_judge_model: str = Field(validation_alias="GOOGLE_JUDGE_MODEL")
    llm_request_delay_seconds: float = Field(
        default=0.0,
        validation_alias="LLM_REQUEST_DELAY_SECONDS",
    )

    database_url: str = Field(
        default="sqlite:///./data/mailcraft.db",
        validation_alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_access_expire_minutes: int = Field(
        default=15,
        validation_alias="JWT_ACCESS_EXPIRE_MINUTES",
    )
    jwt_refresh_expire_days: int = Field(
        default=7,
        validation_alias="JWT_REFRESH_EXPIRE_DAYS",
    )
    upload_max_mb: int = Field(default=10, validation_alias="UPLOAD_MAX_MB")
    upload_dir: str = Field(default="./data/uploads", validation_alias="UPLOAD_DIR")
    humanize_content_enabled: bool = Field(
        default=True,
        validation_alias="HUMANIZE_CONTENT_ENABLED",
    )
    humanize_model: str = Field(
        default="",
        validation_alias="HUMANIZE_MODEL",
    )

    @property
    def strategies(self) -> dict[str, StrategyConfiguration]:
        """Return configured strategy-to-model mappings."""
        return {
            "strategy_a": StrategyConfiguration(
                name="strategy_a",
                model=self.google_model_a,
            ),
            "strategy_b": StrategyConfiguration(
                name="strategy_b",
                model=self.google_model_b,
            ),
        }


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
