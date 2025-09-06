"""
Unit tests for the RetrievalRepo class
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from repositories.retrieval_repo import RetrievalRepo


class TestRetrievalRepo:
    """Test cases for RetrievalRepo"""

    @pytest.fixture
    def mock_uow(self):
        """Create a mock unit of work"""
        mock_session = AsyncMock()
        mock_uow = MagicMock()
        mock_uow.session = mock_session
        return mock_uow

    @pytest.fixture
    def retrieval_repo(self, mock_uow):
        """Create a RetrievalRepo instance with mocked dependencies"""
        return RetrievalRepo(mock_uow)

    @pytest.mark.asyncio
    async def test_get_node_metadata_success(self, retrieval_repo):
        """Test successful retrieval of node metadata"""
        # Mock the database response
        mock_row_dict = {
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

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row_dict)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_metadata(node_id="test-node-123")

        # Verify the result
        assert result is not None
        assert result["node_id"] == "test-node-123"
        assert result["tree_id"] == "test-tree-456"
        assert result["level"] == 2
        assert result["kind"] == "summary"
        assert result["text"] == "This is a summary node"
        assert result["meta"] == {"key": "value"}
        assert result["dataset_id"] == "test-dataset"
        assert result["children_count"] == 3
        assert result["parent_id"] == "parent-node-789"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_metadata_not_found(self, retrieval_repo):
        """Test retrieval of non-existent node metadata"""
        # Mock the database response for not found
        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=None)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_metadata(node_id="non-existent-node")

        # Verify the result
        assert result is None

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_children_success(self, retrieval_repo):
        """Test successful retrieval of node children"""
        # Mock the database response
        mock_rows = [
            {
                "node_id": "child-node-1",
                "tree_id": "test-tree-456",
                "level": 3,
                "kind": "leaf",
                "text": "This is child node 1",
                "child_id": "child-node-1",
            },
            {
                "node_id": "child-node-2",
                "tree_id": "test-tree-456",
                "level": 3,
                "kind": "leaf",
                "text": "This is child node 2",
                "child_id": "child-node-2",
            },
        ]

        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=mock_rows)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_children(node_id="parent-node-123")

        # Verify the result
        assert len(result) == 2
        assert result[0]["node_id"] == "child-node-1"
        assert result[1]["node_id"] == "child-node-2"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()
