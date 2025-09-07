"""MCP (Model Control Protocol) Service for Remote Model Integration

This module provides integration with remote LLM services through the Model Control Protocol.
"""

from .config import MCPConfig, mcp_config
from .raptor_mcp_server import RaptorMCPService

__all__ = [
    "MCPConfig",
    "mcp_config",
    "RaptorMCPService",
]
