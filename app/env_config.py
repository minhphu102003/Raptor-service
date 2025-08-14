from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None

    embed_provider: str = "openai"
    embed_model: str = "text-embedding-3-small"
    embed_dim: int = 1536
    embed_space: str = "cosine"
    embed_normalized: bool = True

    vector_backend: str = "pgvector"
    database_url: str | None = None
    milvus_uri: str | None = None

    rerank_provider: str | None = None
    cohere_api_key: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
