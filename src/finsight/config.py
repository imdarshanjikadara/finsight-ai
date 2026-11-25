"""Application settings, loaded from environment variables or the .env file."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr
    sec_user_agent: str


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them everywhere."""
    return Settings()