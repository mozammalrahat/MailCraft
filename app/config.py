from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class StrategyConfig(BaseModel):
    name: str
    model: str
    template: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MailCraft"
    debug: bool = False
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"
    google_model_a: str = "gemini-2.0-flash"
    google_model_b: str = "gemini-2.0-flash"

    @property
    def strategies(self) -> dict[str, StrategyConfig]:
        return {
            "strategy_a": StrategyConfig(
                name="strategy_a",
                model=self.google_model_a,
                template="strategy_a.jinja",
            ),
            "strategy_b": StrategyConfig(
                name="strategy_b",
                model=self.google_model_b,
                template="strategy_b.jinja",
            ),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
