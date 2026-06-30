"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8081, validation_alias="PORT")
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
    humanize_fact_recall_threshold: float = Field(
        default=0.75,
        validation_alias="HUMANIZE_FACT_RECALL_THRESHOLD",
    )
    llm_max_retries: int = Field(
        default=3,
        validation_alias="LLM_MAX_RETRIES",
    )
    llm_retry_base_delay_seconds: float = Field(
        default=1.0,
        validation_alias="LLM_RETRY_BASE_DELAY_SECONDS",
    )
    llm_retry_max_delay_seconds: float = Field(
        default=30.0,
        validation_alias="LLM_RETRY_MAX_DELAY_SECONDS",
    )
    run_migrations_on_startup: bool = Field(
        default=True,
        validation_alias="RUN_MIGRATIONS_ON_STARTUP",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        validation_alias="RATE_LIMIT_ENABLED",
    )
    log_format: str = Field(
        default="json",
        validation_alias="LOG_FORMAT",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    health_check_llm_enabled: bool = Field(
        default=False,
        validation_alias="HEALTH_CHECK_LLM_ENABLED",
    )
    health_check_llm_timeout_seconds: float = Field(
        default=2.0,
        validation_alias="HEALTH_CHECK_LLM_TIMEOUT_SECONDS",
    )
    storage_backend: str = Field(
        default="local",
        validation_alias="STORAGE_BACKEND",
    )
    s3_bucket: str = Field(
        default="",
        validation_alias="S3_BUCKET",
    )
    aws_region: str = Field(
        default="",
        validation_alias="AWS_REGION",
    )
    aws_access_key_id: str = Field(
        default="",
        validation_alias="AWS_ACCESS_KEY_ID",
    )
    aws_secret_access_key: str = Field(
        default="",
        validation_alias="AWS_SECRET_ACCESS_KEY",
    )
    aws_endpoint_url: str = Field(
        default="",
        validation_alias="AWS_ENDPOINT_URL",
    )
    store_uploaded_resumes: bool = Field(
        default=False,
        validation_alias="STORE_UPLOADED_RESUMES",
    )
    generation_async_enabled: bool = Field(
        default=False,
        validation_alias="GENERATION_ASYNC_ENABLED",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    csrf_enabled: bool = Field(
        default=True,
        validation_alias="CSRF_ENABLED",
    )

    @property
    def effective_log_format(self) -> str:
        """Return text logs in debug mode unless JSON is explicitly configured."""
        if self.log_format == "json":
            return "json"
        if self.debug:
            return "text"
        return self.log_format


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
