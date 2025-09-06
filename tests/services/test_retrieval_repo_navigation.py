from unittest.mock import AsyncMock, MagicMock

import pytest

from repositories.retrieval_repo import RetrievalRepo


class TestRetrievalRepoNavigation:
    """Test cases for RetrievalRepo navigation functions"""

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
    async def test_get_node_parent(self, retrieval_repo):
        """Test get_node_parent repository function"""
        # Mock the database response
        mock_row_dict = {
            "node_id": "parent_123",
            "tree_id": "tree_123",
            "level": 1,
            "kind": "summary",
            "text": "Parent node text",
        }

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row_dict)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_parent(node_id="child_123")

        # Verify the result
        assert result is not None
        assert result["node_id"] == "parent_123"
        assert result["level"] == 1
        assert result["kind"] == "summary"
        assert result["text"] == "Parent node text"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_parent_not_found(self, retrieval_repo):
        """Test get_node_parent when parent doesn't exist"""
        # Mock the database response (no parent found)
        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=None)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_parent(node_id="orphan_node")

        # Verify the result
        assert result is None

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_siblings(self, retrieval_repo):
        """Test get_node_siblings repository function"""
        # Mock the database response
        mock_rows = [
            {
                "node_id": "sibling_1",
                "tree_id": "tree_123",
                "level": 2,
                "kind": "leaf",
                "text": "Sibling 1 text",
            },
            {
                "node_id": "sibling_2",
                "tree_id": "tree_123",
                "level": 2,
                "kind": "leaf",
                "text": "Sibling 2 text",
            },
        ]

        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=mock_rows)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_siblings(node_id="test_node")

        # Verify the result
        assert len(result) == 2
        assert result[0]["node_id"] == "sibling_1"
        assert result[1]["node_id"] == "sibling_2"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_siblings_none_found(self, retrieval_repo):
        """Test get_node_siblings when no siblings exist"""
        # Mock the database response (no siblings found)
        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=[])
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_siblings(node_id="only_child")

        # Verify the result
        assert result == []

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_path_to_root(self, retrieval_repo):
        """Test get_path_to_root repository function"""
        # Mock the database response
        mock_rows = [
            {
                "node_id": "node_123",
                "tree_id": "tree_123",
                "level": 2,
                "kind": "summary",
                "text": "Current node text",
            },
            {
                "node_id": "parent_123",
                "tree_id": "tree_123",
                "level": 1,
                "kind": "summary",
                "text": "Parent node text",
            },
            {
                "node_id": "root_123",
                "tree_id": "tree_123",
                "level": 0,
                "kind": "root",
                "text": "Root node text",
            },
        ]

        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=mock_rows)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_path_to_root(node_id="node_123")

        # Verify the result
        assert len(result) == 3
        assert result[0]["node_id"] == "node_123"
        assert result[1]["node_id"] == "parent_123"
        assert result[2]["node_id"] == "root_123"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_path_to_root_single_node(self, retrieval_repo):
        """Test get_path_to_root when node is already root"""
        # Mock the database response (node is root)
        mock_rows = [
            {
                "node_id": "root_123",
                "tree_id": "tree_123",
                "level": 0,
                "kind": "root",
                "text": "Root node text",
            }
        ]

        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=mock_rows)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_path_to_root(node_id="root_123")

        # Verify the result
        assert len(result) == 1
        assert result[0]["node_id"] == "root_123"
        assert result[0]["kind"] == "root"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_texts_by_ids(self, retrieval_repo):
        """Test get_node_texts_by_ids repository function"""
        # Mock the database response
        mock_rows = [
            {"node_id": "node_1", "text": "Text for node 1"},
            {"node_id": "node_2", "text": "Text for node 2"},
        ]

        mock_result = MagicMock()
        mock_result.all = MagicMock(return_value=mock_rows)
        mock_result.mappings = MagicMock(return_value=mock_result)

        # Mock the session execute method
        retrieval_repo.session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await retrieval_repo.get_node_texts_by_ids(node_ids=["node_1", "node_2"])

        # Verify the result
        assert len(result) == 2
        assert result[0]["node_id"] == "node_1"
        assert result[0]["text"] == "Text for node 1"
        assert result[1]["node_id"] == "node_2"
        assert result[1]["text"] == "Text for node 2"

        # Verify the SQL query was executed
        retrieval_repo.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node_texts_by_ids_empty(self, retrieval_repo):
        """Test get_node_texts_by_ids with empty node_ids list"""
        # Call the method
        result = await retrieval_repo.get_node_texts_by_ids(node_ids=[])

        # Verify the result
        assert result == []

        # Verify no SQL query was executed
        retrieval_repo.session.execute.assert_not_called()
