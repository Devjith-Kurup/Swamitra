from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(_BACKEND_ROOT / ".env", _REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Swamitra"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql://USER:PASSWORD@localhost:5432/DATABASE_NAME"
    
    # Weather configuration
    weather_provider: str = "open-meteo"
    weather_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
