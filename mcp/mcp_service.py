import logging
from typing import Any, Dict, List, Optional

from services.providers.model_registry import ModelRegistry

from .mcp_client import MCPClient, MCPModelAdapter

logger = logging.getLogger("raptor.mcp.service")


class MCPService:
    """Service for managing remote MCP model integrations"""

    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.mcp_adapters: Dict[str, MCPModelAdapter] = {}

    def register_mcp_endpoint(self, name: str, base_url: str, api_key: Optional[str] = None):
        """Register a new MCP endpoint"""
        client = MCPClient(base_url, api_key)
        adapter = MCPModelAdapter(client)

        self.mcp_clients[name] = client
        self.mcp_adapters[name] = adapter

        # Register models that should route to this MCP
        # This would typically be configured in a settings file
        model_routes = {
            "mcp": name,  # Generic route for all models through this MCP
        }

        for model_alias, mcp_name in model_routes.items():
            if mcp_name == name:
                # Add to model registry routing
                self.model_registry._route[model_alias] = f"mcp_{name}"
                self.model_registry._pretty[f"mcp_{name}"] = f"MCP:{name}"

        logger.info(f"Registered MCP endpoint: {name} -> {base_url}")

    def get_mcp_client(self, name: str) -> Optional[MCPClient]:
        """Get MCP client by name"""
        return self.mcp_clients.get(name)

    def get_mcp_adapter(self, name: str) -> Optional[MCPModelAdapter]:
        """Get MCP adapter by name"""
        return self.mcp_adapters.get(name)

    async def chat_completions(
        self,
        mcp_name: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ):
        """Send chat completion request to specific MCP service"""
        adapter = self.get_mcp_adapter(mcp_name)
        if not adapter:
            raise ValueError(f"MCP endpoint '{mcp_name}' not registered")

        async with adapter.mcp_client as client:
            return await client.chat_completions(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=stream,
            )

    async def summarize(
        self,
        mcp_name: str,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Summarize text using specific MCP service"""
        adapter = self.get_mcp_adapter(mcp_name)
        if not adapter:
            raise ValueError(f"MCP endpoint '{mcp_name}' not registered")

        async with adapter.mcp_client as client:
            return await adapter.summarize(
                prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature
            )
