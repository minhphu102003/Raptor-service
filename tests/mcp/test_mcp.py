"""
Tests for MCP (Model Control Protocol) Service
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp.mcp_client import MCPClient, MCPModelAdapter
from mcp.mcp_service import MCPService


@pytest.fixture
def mock_model_registry():
    """Create a mock model registry for testing"""
    return Mock()


@pytest.fixture
def mcp_service(mock_model_registry):
    """Create an MCP service instance for testing"""
    return MCPService(mock_model_registry)


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization"""
    client = MCPClient("http://test-server.com", "test-key")
    assert client.base_url == "http://test-server.com"
    assert client.api_key == "test-key"


@pytest.mark.asyncio
async def test_mcp_service_registration(mcp_service):
    """Test MCP service registration"""
    # This would normally register an endpoint
    # For now, we just test the service exists
    assert mcp_service is not None
    assert hasattr(mcp_service, "register_mcp_endpoint")


@pytest.mark.asyncio
async def test_mcp_model_adapter():
    """Test MCP model adapter"""
    mock_client = AsyncMock()
    adapter = MCPModelAdapter(mock_client)

    assert adapter.mcp_client == mock_client
    assert hasattr(adapter, "chat_completions")
    assert hasattr(adapter, "summarize")


if __name__ == "__main__":
    pytest.main([__file__])
