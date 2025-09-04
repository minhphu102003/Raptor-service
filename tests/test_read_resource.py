import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.resources import read_resource


@pytest.mark.asyncio
async def test_read_resource_with_container():
    """Test read_resource with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_retrieval_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_retrieval_repo

    # Configure mock retrieval repo to return specific data
    mock_node_data = {
        "node_id": "node_123",
        "tree_id": "tree_123",
        "level": 2,
        "kind": "summary",
        "text": "This is the actual content of the node from the database.",
        "dataset_id": "dataset_123",
    }
    mock_retrieval_repo.get_node_metadata.return_value = mock_node_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await read_resource("raptor://dataset_123/nodes/node_123", container=mock_container)

    # Verify the result
    assert "contents" in result
    assert len(result["contents"]) == 1
    assert result["contents"][0]["uri"] == "raptor://dataset_123/nodes/node_123"
    assert result["contents"][0]["mimeType"] == "text/plain"
    assert "This is the actual content" in result["contents"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_retrieval_repo.get_node_metadata.assert_called_once_with(node_id="node_123")


@pytest.mark.asyncio
async def test_read_resource_without_container():
    """Test read_resource without container (backward compatibility)"""
    # Call the function without container
    result = await read_resource("raptor://dataset_123/nodes/node_123", container=None)

    # Verify the result (should use simulated data)
    assert "contents" in result
    assert len(result["contents"]) == 1
    assert result["contents"][0]["uri"] == "raptor://dataset_123/nodes/node_123"
    assert result["contents"][0]["mimeType"] == "text/plain"
    assert "detailed content that would be retrieved" in result["contents"][0]["text"]


@pytest.mark.asyncio
async def test_read_resource_node_not_found():
    """Test read_resource when node is not found in database"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_retrieval_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_retrieval_repo

    # Configure mock retrieval repo to return None (node not found)
    mock_retrieval_repo.get_node_metadata.return_value = None

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function and expect an exception
    with pytest.raises(Exception, match="Node node_123 not found"):
        await read_resource("raptor://dataset_123/nodes/node_123", container=mock_container)


@pytest.mark.asyncio
async def test_read_resource_invalid_uri():
    """Test read_resource with invalid URI"""
    # Call the function with invalid URI
    result = await read_resource("invalid://uri", container=None)

    # Verify the result (should return default response)
    assert "contents" in result
    assert len(result["contents"]) == 1
    assert result["contents"][0]["uri"] == "invalid://uri"
    assert "Resource content for invalid://uri" in result["contents"][0]["text"]
