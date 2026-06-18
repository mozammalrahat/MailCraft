from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StrategyConfig(BaseModel):
    name: str
    model: str


class Settings(BaseSettings):
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

    @property
    def strategies(self) -> dict[str, StrategyConfig]:
        return {
            "strategy_a": StrategyConfig(
                name="strategy_a",
                model=self.google_model_a,
            ),
            "strategy_b": StrategyConfig(
                name="strategy_b",
                model=self.google_model_b,
            ),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
