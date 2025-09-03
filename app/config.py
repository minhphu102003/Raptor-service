import os

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    dsn: str = ""
    voyage_api_key: str = ""
    voyage_model: str = "voyage-context-3"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    api_prefix: str = "/v1"
    pg_async_dsn: str = ""
    debug: bool = False

    # MCP settings
    mcp_enabled: bool = True  # Flag to enable/disable MCP server

    vector: VectorSettings = VectorSettings()

    @computed_field
    @property
    def db_echo(self) -> bool:
        return self.debug


# Create settings instance
settings = Settings()

# Override settings from environment variables
# This allows for runtime configuration
for key, value in os.environ.items():
    if key.startswith("APP_"):
        setattr(settings, key[4:].lower(), value)
    elif key.startswith("VECTOR_"):
        setattr(settings.vector, key[7:].lower(), value)
