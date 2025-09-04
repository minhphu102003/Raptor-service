"""
Unit tests for the RAG tools
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.rag_tools import rag_node_children, rag_node_get


class TestRAGTools:
    """Test cases for RAG tools"""

    @pytest.mark.asyncio
    async def test_rag_node_get_with_container_success(self):
        """Test successful retrieval of node metadata with container"""
        # Mock the container and its methods
        mock_container = MagicMock()
        mock_uow = MagicMock()
        mock_repo = MagicMock()

        # Set up the container mock
        mock_container.make_uow.return_value = mock_uow
        mock_container.make_retrieval_repo.return_value = mock_repo

        # Mock the repo response
        mock_node_data = {
            "node_id": "test-node-123",
            "tree_id": "test-tree-456",
            "level": 2,
            "kind": "summary",
            "text": "This is a summary node",
            "meta": {"key": "value"},
            "dataset_id": "test-dataset",
            "children_count": 3,
            "parent_id": "parent-node-789",
        }
        mock_repo.get_node_metadata = AsyncMock(return_value=mock_node_data)

        # Mock the async context manager
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)

        # Call the function
        result = await rag_node_get("test-node-123", container=mock_container)

        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Node metadata" in result["content"][0]["text"]

        # Verify the container methods were called
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
        mock_repo.get_node_metadata.assert_called_once_with(node_id="test-node-123")

    @pytest.mark.asyncio
    async def test_rag_node_get_with_container_not_found(self):
        """Test retrieval of non-existent node with container"""
        # Mock the container and its methods
        mock_container = MagicMock()
        mock_uow = MagicMock()
        mock_repo = MagicMock()

        # Set up the container mock
        mock_container.make_uow.return_value = mock_uow
        mock_container.make_retrieval_repo.return_value = mock_repo

        # Mock the repo response for not found
        mock_repo.get_node_metadata = AsyncMock(return_value=None)

        # Mock the async context manager
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)

        # Call the function
        result = await rag_node_get("non-existent-node", container=mock_container)

        # Verify the result is an error
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()

        # Verify the container methods were called
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
        mock_repo.get_node_metadata.assert_called_once_with(node_id="non-existent-node")

    @pytest.mark.asyncio
    async def test_rag_node_get_without_container(self):
        """Test retrieval of node metadata without container (should return error)"""
        # Call the function without container
        result = await rag_node_get("test-node-123", container=None)

        # Verify the result is an error
        assert result["isError"] is True
        assert "container is required" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_rag_node_children_with_container_success(self):
        """Test successful retrieval of node children with container"""
        # Mock the container and its methods
        mock_container = MagicMock()
        mock_uow = MagicMock()
        mock_repo = MagicMock()

        # Set up the container mock
        mock_container.make_uow.return_value = mock_uow
        mock_container.make_retrieval_repo.return_value = mock_repo

        # Mock the repo response
        mock_children_data = [
            {"node_id": "child-node-1", "level": 3, "kind": "leaf", "text": "This is child node 1"},
            {"node_id": "child-node-2", "level": 3, "kind": "leaf", "text": "This is child node 2"},
        ]
        mock_repo.get_node_children = AsyncMock(return_value=mock_children_data)

        # Mock the async context manager
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)

        # Call the function
        result = await rag_node_children("parent-node-123", container=mock_container)

        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Child nodes" in result["content"][0]["text"]

        # Verify the container methods were called
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
        mock_repo.get_node_children.assert_called_once_with(node_id="parent-node-123")

    @pytest.mark.asyncio
    async def test_rag_node_children_without_container(self):
        """Test retrieval of node children without container (fallback to simulated data)"""
        # Call the function without container
        result = await rag_node_children("parent-node-123", container=None)

        # Verify the result (should be simulated data)
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Child nodes" in result["content"][0]["text"]
        assert "child_0_of_parent-node-123" in result["content"][0]["text"]
