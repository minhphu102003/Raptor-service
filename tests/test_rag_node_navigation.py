import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.rag_tools import rag_node_navigation


@pytest.mark.asyncio
async def test_rag_node_navigation_with_container_parent():
    """Test rag_node_navigation with container for parent direction"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_parent_data = {
        "node_id": "parent_node_123",
        "level": 1,
        "kind": "summary",
        "text": "Parent node text",
    }
    mock_repo.get_node_parent.return_value = mock_parent_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_navigation("test_node_123", "parent", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "Parent" in str(result["content"][0]["text"])
    assert "parent_node_123" in str(result["content"][0]["text"])

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_parent.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_navigation_with_container_siblings():
    """Test rag_node_navigation with container for siblings direction"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_siblings_data = [
        {"node_id": "sibling_1", "level": 2, "kind": "leaf", "text": "Sibling 1 text"},
        {"node_id": "sibling_2", "level": 2, "kind": "leaf", "text": "Sibling 2 text"},
    ]
    mock_repo.get_node_siblings.return_value = mock_siblings_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_navigation("test_node_123", "siblings", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "Siblings" in str(result["content"][0]["text"])
    assert "sibling_1" in str(result["content"][0]["text"])
    assert "sibling_2" in str(result["content"][0]["text"])

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_siblings.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_navigation_with_container_invalid_direction():
    """Test rag_node_navigation with container for invalid direction"""
    # Create mock container
    mock_container = MagicMock()

    # Call the function with invalid direction
    result = await rag_node_navigation(
        "test_node_123", "invalid_direction", container=mock_container
    )

    # Verify the result is an error
    assert result["isError"]
    assert "Invalid direction" in str(result["content"][0]["text"])


@pytest.mark.asyncio
async def test_rag_node_navigation_without_container_parent():
    """Test rag_node_navigation without container for parent direction (backward compatibility)"""
    # Call the function without container
    result = await rag_node_navigation("test_node_123", "parent", container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "Parent" in str(result["content"][0]["text"])
    assert "parent_of_test_node_123" in str(result["content"][0]["text"])


@pytest.mark.asyncio
async def test_rag_node_navigation_without_container_siblings():
    """Test rag_node_navigation without container for siblings direction (backward compatibility)"""
    # Call the function without container
    result = await rag_node_navigation("test_node_123", "siblings", container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "Siblings" in str(result["content"][0]["text"])
    assert "sibling_0_of_test_node_123" in str(result["content"][0]["text"])
    assert "sibling_1_of_test_node_123" in str(result["content"][0]["text"])


@pytest.mark.asyncio
async def test_rag_node_navigation_without_container_invalid_direction():
    """Test rag_node_navigation without container for invalid direction (backward compatibility)"""
    # Call the function with invalid direction
    result = await rag_node_navigation("test_node_123", "invalid_direction", container=None)

    # Verify the result is an error
    assert result["isError"]
    assert "Invalid direction" in str(result["content"][0]["text"])


@pytest.mark.asyncio
async def test_rag_node_navigation_parent_not_found():
    """Test rag_node_navigation when parent node is not found"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return None (parent not found)
    mock_repo.get_node_parent.return_value = None

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_navigation("test_node_123", "parent", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "Parent" in str(result["content"][0]["text"])
    assert "None" in str(result["content"][0]["text"])

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_parent.assert_called_once_with(node_id="test_node_123")
