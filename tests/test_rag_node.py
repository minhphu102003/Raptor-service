import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.rag_node import rag_node_children, rag_node_get, rag_node_navigation


@pytest.mark.asyncio
async def test_rag_node_get_with_container():
    """Test rag_node_get with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_node_data = {
        "node_id": "node_123",
        "tree_id": "tree_123",
        "level": 2,
        "kind": "summary",
        "text": "This is the node content.",
        "meta": {"key": "value"},
        "dataset_id": "dataset_123",
        "children_count": 3,
        "parent_id": "parent_123",
    }
    mock_repo.get_node_metadata.return_value = mock_node_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_get("test_node_123", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Node metadata" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_metadata.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_get_without_container():
    """Test rag_node_get without container (should raise error)"""
    # Call the function without container - should raise an error
    with pytest.raises(ValueError, match="Container is required"):
        await rag_node_get("test_node_123", container=None)


@pytest.mark.asyncio
async def test_rag_node_get_node_not_found():
    """Test rag_node_get when node is not found"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return None (node not found)
    mock_repo.get_node_metadata.return_value = None

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_get("test_node_123", container=mock_container)

    # Verify the result is an error
    assert result["isError"]
    assert "Node test_node_123 not found" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_node_children_with_container():
    """Test rag_node_children with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_children_data = [
        {
            "node_id": "child_1",
            "level": 1,
            "kind": "leaf",
            "text": "Child 1 content",
        },
        {
            "node_id": "child_2",
            "level": 1,
            "kind": "leaf",
            "text": "Child 2 content",
        },
    ]
    mock_repo.get_node_children.return_value = mock_children_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_children("test_node_123", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Child nodes" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_children.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_children_without_container():
    """Test rag_node_children without container (backward compatibility)"""
    # Call the function without container
    result = await rag_node_children("test_node_123", container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Child nodes" in result["content"][0]["text"]
    assert "child_0_of_test_node_123" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_node_navigation_with_container_parent():
    """Test rag_node_navigation with container for parent navigation"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_parent_data = {
        "node_id": "parent_123",
        "level": 1,
        "kind": "summary",
        "text": "Parent content",
    }
    mock_repo.get_node_parent.return_value = mock_parent_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_navigation("test_node_123", "parent", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Parent" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_parent.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_navigation_with_container_siblings():
    """Test rag_node_navigation with container for siblings navigation"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_siblings_data = [
        {
            "node_id": "sibling_1",
            "level": 2,
            "kind": "summary",
            "text": "Sibling 1 content",
        },
        {
            "node_id": "sibling_2",
            "level": 2,
            "kind": "summary",
            "text": "Sibling 2 content",
        },
    ]
    mock_repo.get_node_siblings.return_value = mock_siblings_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_node_navigation("test_node_123", "siblings", container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Siblings" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    mock_repo.get_node_siblings.assert_called_once_with(node_id="test_node_123")


@pytest.mark.asyncio
async def test_rag_node_navigation_without_container():
    """Test rag_node_navigation without container (backward compatibility)"""
    # Call the function without container for parent navigation
    result_parent = await rag_node_navigation("test_node_123", "parent", container=None)

    # Verify the result (should use simulated data)
    assert not result_parent["isError"]
    assert "content" in result_parent
    assert len(result_parent["content"]) > 0
    assert "Parent" in result_parent["content"][0]["text"]
    assert "parent_of_test_node_123" in result_parent["content"][0]["text"]

    # Call the function without container for siblings navigation
    result_siblings = await rag_node_navigation("test_node_123", "siblings", container=None)

    # Verify the result (should use simulated data)
    assert not result_siblings["isError"]
    assert "content" in result_siblings
    assert len(result_siblings["content"]) > 0
    assert "Siblings" in result_siblings["content"][0]["text"]
    assert "sibling_0_of_test_node_123" in result_siblings["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_node_navigation_invalid_direction():
    """Test rag_node_navigation with invalid direction"""
    # Call the function with invalid direction
    result = await rag_node_navigation("test_node_123", "invalid", container=None)

    # Verify the result is an error
    assert result["isError"]
    assert "Invalid direction" in result["content"][0]["text"]
