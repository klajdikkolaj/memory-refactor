from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "postgresql+asyncpg://memory_refactor:memory_refactor@localhost:5432/memory_refactor"
    )
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "memory-refactor"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    litellm_base_url: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
