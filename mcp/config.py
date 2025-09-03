from typing import Dict, Optional

from pydantic import BaseModel


class MCPConfig(BaseModel):
    """Configuration for Model Control Protocol endpoints"""

    # MCP endpoint configurations
    endpoints: Dict[str, Dict[str, str]] = {
        "default": {
            "base_url": "http://localhost:8001",
            "api_key": "",  # Optional API key
        }
    }

    # Default summarization settings for MCP models
    summarization_max_tokens: int = 1000
    summarization_temperature: float = 0.3

    # Throttling settings
    rpm_limit: int = 60  # Requests per minute
    max_concurrent: int = 5

    class Config:
        env_prefix = "MCP_"


# Global MCP configuration instance
mcp_config = MCPConfig()
