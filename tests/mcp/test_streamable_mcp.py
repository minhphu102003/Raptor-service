import asyncio
from unittest.mock import Mock, patch

import pytest

# Initialize Streamable MCP components as None
StreamableMCPService = None
create_streamable_mcp_service = None
STREAMABLE_MCP_IMPORT_SUCCESS = False

# Try to import Streamable MCP components
try:
    from mcp_local.streamable_mcp_server import StreamableMCPService, create_streamable_mcp_service

    STREAMABLE_MCP_IMPORT_SUCCESS = True
except ImportError:
    pass


@pytest.mark.asyncio
async def test_streamable_mcp_service_initialization():
    """Test that Streamable MCP service initializes correctly"""
    if not STREAMABLE_MCP_IMPORT_SUCCESS or StreamableMCPService is None:
        pytest.skip("Streamable MCP components not available")

    # Create a mock container
    mock_container = Mock()

    # Create Streamable MCP service
    streamable_mcp_service = StreamableMCPService(mock_container)

    # Check that service was created
    assert streamable_mcp_service is not None
    assert hasattr(streamable_mcp_service, "container")
    assert hasattr(streamable_mcp_service, "mcp_server")
    assert hasattr(streamable_mcp_service, "sse_transport")


@pytest.mark.asyncio
async def test_streamable_mcp_service_without_container():
    """Test that Streamable MCP service can be created without container"""
    if not STREAMABLE_MCP_IMPORT_SUCCESS or StreamableMCPService is None:
        pytest.skip("Streamable MCP components not available")

    # Create Streamable MCP service without container
    streamable_mcp_service = StreamableMCPService()

    # Check that service was created
    assert streamable_mcp_service is not None
    assert streamable_mcp_service.container is None
    assert hasattr(streamable_mcp_service, "mcp_server")
    assert hasattr(streamable_mcp_service, "sse_transport")


@pytest.mark.asyncio
async def test_create_streamable_mcp_service_function():
    """Test that create_streamable_mcp_service function works"""
    if not STREAMABLE_MCP_IMPORT_SUCCESS or create_streamable_mcp_service is None:
        pytest.skip("Streamable MCP components not available")

    # Test with container
    mock_container = Mock()
    service_with_container = create_streamable_mcp_service(mock_container)
    assert service_with_container is not None
    assert service_with_container.container == mock_container

    # Test without container
    service_without_container = create_streamable_mcp_service()
    assert service_without_container is not None
    assert service_without_container.container is None


if __name__ == "__main__":
    pytest.main([__file__])
