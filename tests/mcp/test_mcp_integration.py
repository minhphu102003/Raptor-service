"""
Tests for MCP Integration with RAPTOR Service
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Initialize MCP components as None
FastMCP = None
RaptorMCPService = None
SSEManager = None
MCP_IMPORT_SUCCESS = False

# Try to import MCP components
try:
    from mcp.raptor_mcp_server import RaptorMCPService
    from mcp.server.fastmcp import FastMCP
    from mcp.sse_endpoint import SSEManager

    MCP_IMPORT_SUCCESS = True
except ImportError:
    pass


@pytest.mark.asyncio
async def test_mcp_service_initialization():
    """Test that MCP service initializes correctly"""
    if not MCP_IMPORT_SUCCESS or RaptorMCPService is None:
        pytest.skip("MCP components not available")

    # Create a mock container
    mock_container = Mock()

    # Create MCP service
    mcp_service = RaptorMCPService(mock_container)

    # Check that service was created
    assert mcp_service is not None
    assert hasattr(mcp_service, "mcp")


@pytest.mark.asyncio
async def test_mcp_tools_registration():
    """Test that MCP tools are registered"""
    if not MCP_IMPORT_SUCCESS or RaptorMCPService is None:
        pytest.skip("MCP components not available")

    # Create a mock container
    mock_container = Mock()

    # Create MCP service
    mcp_service = RaptorMCPService(mock_container)

    # Check that MCP server exists
    mcp_server = mcp_service.get_mcp_server()
    assert mcp_server is not None


@pytest.mark.asyncio
async def test_sse_manager():
    """Test SSE manager functionality"""
    if not MCP_IMPORT_SUCCESS or SSEManager is None:
        pytest.skip("MCP components not available")

    # Create SSE manager
    sse_manager = SSEManager()

    # Test connection creation
    conn_id, queue = await sse_manager.connect()
    assert conn_id is not None
    assert queue is not None

    # Test connection listing
    assert conn_id in sse_manager.connections

    # Test disconnection
    sse_manager.disconnect(conn_id)
    assert conn_id not in sse_manager.connections


@pytest.mark.asyncio
async def test_tool_functions():
    """Test that tool functions work correctly"""
    if not MCP_IMPORT_SUCCESS or RaptorMCPService is None:
        pytest.skip("MCP components not available")

    # Create a mock container
    mock_container = Mock()

    # Create MCP service
    mcp_service = RaptorMCPService(mock_container)

    # Test that tools exist (we can't easily test the actual tool registration
    # without running the full server, but we can check the service structure)
    assert hasattr(mcp_service, "_register_tools")


if __name__ == "__main__":
    pytest.main([__file__])
