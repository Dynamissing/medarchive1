from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = Field(default="MedArchive / MedPartners", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = Field(default="INFO", validation_alias="APP_LOG_LEVEL")
    backend_host: str = Field(default="127.0.0.1", validation_alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, validation_alias="BACKEND_PORT")
    cors_origins: str = Field(default="http://localhost:3000", validation_alias="CORS_ORIGINS")
    file_storage_root: Path = Field(default=PROJECT_DIR / "data" / "storage", validation_alias="FILE_STORAGE_ROOT")
    database_url: str = Field(
        default="postgresql+psycopg://medarchive:medarchive@localhost:5432/medarchive",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    celery_task_always_eager: bool = Field(default=False, validation_alias="CELERY_TASK_ALWAYS_EAGER")
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", validation_alias="ADMIN_PASSWORD")
    admin_token_secret: str = Field(default="change-me-for-demo", validation_alias="ADMIN_TOKEN_SECRET")
    admin_token_ttl_seconds: int = Field(default=3600, validation_alias="ADMIN_TOKEN_TTL_SECONDS")
    match_auto_accept_threshold: float = Field(default=0.94, validation_alias="MATCH_AUTO_ACCEPT_THRESHOLD")
    match_needs_review_threshold: float = Field(default=0.72, validation_alias="MATCH_NEEDS_REVIEW_THRESHOLD")
    match_enable_embeddings: bool = Field(default=False, validation_alias="MATCH_ENABLE_EMBEDDINGS")
    match_enable_openrouter: bool = Field(default=False, validation_alias="MATCH_ENABLE_OPENROUTER")
    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    currency_conversion_rates: str = Field(default="{}", validation_alias="CURRENCY_CONVERSION_RATES")

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def debug(self) -> bool:
        return self.app_debug


@lru_cache
def get_settings() -> Settings:
    return Settings()
