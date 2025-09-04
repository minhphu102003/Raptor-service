import os

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    dsn: str = ""
    voyage_api_key: str = ""
    voyage_model: str = "voyage-context-3"


class MCPSettings(BaseSettings):
    """MCP (Model Context Protocol) settings"""

    model_config = SettingsConfigDict(env_prefix="MCP_")

    enabled: bool = True
    endpoints_default_base_url: str = "http://localhost:8001"
    endpoints_default_api_key: str = ""
    summarization_max_tokens: int = 1000
    summarization_temperature: float = 0.3
    rpm_limit: int = 60
    max_concurrent: int = 5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    api_prefix: str = "/v1"
    pg_async_dsn: str = ""
    debug: bool = False

    # MCP settings
    mcp: MCPSettings = MCPSettings()

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
        field_name = key[4:].lower()
        # Only set attributes that exist in the Settings class
        if hasattr(settings, field_name):
            setattr(settings, field_name, value)
    elif key.startswith("VECTOR_"):
        field_name = key[7:].lower()
        # Only set attributes that exist in the VectorSettings class
        if hasattr(settings.vector, field_name):
            setattr(settings.vector, field_name, value)
    elif key.startswith("MCP_"):
        # Handle MCP settings
        parts = key[4:].lower().split("_")
        if len(parts) >= 2:
            # For nested settings like MCP_ENDPOINTS_DEFAULT_BASE_URL
            if parts[0] == "endpoints" and len(parts) >= 3:
                # Handle endpoints nested structure
                # This is a simplified approach - in practice, you might want a more robust solution
                pass
            elif hasattr(settings.mcp, "_".join(parts)):
                setattr(settings.mcp, "_".join(parts), value)
