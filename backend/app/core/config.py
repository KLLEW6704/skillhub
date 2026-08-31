from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SkillHub API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./skillhub.db"
    jwt_secret: str = "change-me-before-production"
    access_token_minutes: int = 30
    frontend_origin: str = "http://localhost:5173"
    upload_dir: Path = Path("uploads")
    max_upload_mb: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
