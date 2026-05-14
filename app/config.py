from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="TalentFit Engine")
    use_optional_llm: bool = Field(default=False)
    optional_llm_provider: str | None = None
    optional_llm_api_key: str | None = None
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    max_upload_mb: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
