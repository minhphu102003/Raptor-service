from pydantic import BaseModel
from pydantic_settings import BaseSettings


class VectorCfg(BaseModel):
    driver: str = "pgvector"
    dsn: str
    name: str = "kb.docs"
    namespace: str | None = None
    metric: str = "cosine"


class Settings(BaseSettings):
    api_prefix: str = ""
    openai_api_key: str | None = None

    vector: VectorCfg

    pg_dsn: str | None = None

    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"


settings = Settings()
