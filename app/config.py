from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorCfg(BaseModel):
    driver: str = "pgvector"
    dsn: str
    name: str = "kb.docs"
    namespace: str | None = None
    metric: str = "cosine"


class Settings(BaseSettings):
    api_prefix: str = ""
    openai_api_key: str | None = None
    voyageai_key: Optional[str] = None

    vector: VectorCfg
    pg_async_dsn: str | None = None
    pg_dsn: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
