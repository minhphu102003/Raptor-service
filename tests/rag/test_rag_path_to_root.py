import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# Updated import to use the new separate module
from mcp_local.tools.rag_navigation import rag_path_to_root


@pytest.mark.asyncio
async def test_rag_path_to_root_with_container():
    """Test rag_path_to_root with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_path_data = [
        {"node_id": "node_123", "level": 2, "kind": "summary", "text": "Current node text"},
        {"node_id": "parent_123", "level": 1, "kind": "summary", "text": "Parent node text"},
        {"node_id": "root_123", "level": 0, "kind": "root", "text": "Root node text"},
    ]
    mock_repo.get_path_to_root.return_value = mock_path_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_path_to_root("test_node_123", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "Path to root" in str(result["content"][0]["text"])

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_path_to_root.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_path_to_root_without_container():
    """Test rag_path_to_root without container (backward compatibility)"""
    # Call the function without container
    result = await rag_path_to_root("test_node_123", container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "Path to root" in str(result["content"][0]["text"])
