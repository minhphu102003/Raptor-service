import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Initialize to None to avoid "possibly unbound" error
list_datasets = None
LIST_DATASETS_IMPORT_SUCCESS = False

# Try to import the list_datasets function
try:
    from mcp_local.tools.base_tools import list_datasets

    LIST_DATASETS_IMPORT_SUCCESS = True
except ImportError:
    LIST_DATASETS_IMPORT_SUCCESS = False
    list_datasets = None  # Explicitly set to None in case of import failure


@pytest.mark.asyncio
async def test_list_datasets_without_container():
    """Test list_datasets function without container (simulated data)"""
    if not LIST_DATASETS_IMPORT_SUCCESS or list_datasets is None:
        pytest.skip("list_datasets function not available")

    # Call list_datasets without container
    result = await list_datasets()

    # Check that result is a dictionary with expected keys
    assert isinstance(result, dict)
    assert "content" in result
    assert "isError" in result
    assert result["isError"] is False

    # Check content structure
    content = result["content"]
    assert isinstance(content, list)
    assert len(content) > 0
    assert content[0]["type"] == "text"

    # Parse the JSON content
    datasets = json.loads(content[0]["text"])
    assert isinstance(datasets, list)
    assert len(datasets) > 0

    # Check that each dataset has the expected properties
    for dataset in datasets:
        assert "id" in dataset
        assert "name" in dataset
        assert "description" in dataset
        assert "document_count" in dataset
        assert "chunk_count" in dataset
        assert "embedding_count" in dataset
        assert "tree_count" in dataset
        assert "created_at" in dataset
        assert "last_updated" in dataset
        assert "status" in dataset


@pytest.mark.asyncio
async def test_list_datasets_with_container():
    """Test list_datasets function with container (real data)"""
    if not LIST_DATASETS_IMPORT_SUCCESS or list_datasets is None:
        pytest.skip("list_datasets function not available")

    # Create mock container and related objects
    mock_container = Mock()
    mock_uow = Mock()
    mock_dataset_repo = Mock()

    # Set up the mock chain
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_dataset_repo.return_value = mock_dataset_repo

    # Mock dataset data
    mock_datasets = [
        {
            "id": "test_dataset_1",
            "name": "Test Dataset 1",
            "description": "Test dataset for unit testing",
            "document_count": 3,
            "created_at": "2023-01-01T00:00:00Z",
            "last_updated": "2023-01-02T00:00:00Z",
        }
    ]

    mock_detailed_info = {
        "id": "test_dataset_1",
        "name": "Test Dataset 1",
        "description": "Test dataset for unit testing",
        "document_count": 3,
        "chunk_count": 15,
        "embedding_count": 15,
        "tree_count": 1,
        "created_at": "2023-01-01T00:00:00Z",
        "last_updated": "2023-01-02T00:00:00Z",
        "status": "active",
        "total_tokens": 4500,
        "embedding_models": ["voyage-context-3"],
        "processing_status": "completed",
    }

    # Set up mock methods
    mock_dataset_repo.list_datasets = AsyncMock(return_value=mock_datasets)
    mock_dataset_repo.get_dataset_info = AsyncMock(return_value=mock_detailed_info)

    # Mock the async context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call list_datasets with container
    result = await list_datasets(container=mock_container)

    # Check that result is a dictionary with expected keys
    assert isinstance(result, dict)
    assert "content" in result
    assert "isError" in result
    assert result["isError"] is False

    # Verify that the mock methods were called
    mock_container.make_uow.assert_called_once()
    mock_container.make_dataset_repo.assert_called_once_with(mock_uow)
    mock_dataset_repo.list_datasets.assert_awaited_once()
    mock_dataset_repo.get_dataset_info.assert_awaited_once_with("test_dataset_1")

    # Check content structure
    content = result["content"]
    assert isinstance(content, list)
    assert len(content) > 0
    assert content[0]["type"] == "text"

    # Parse the JSON content
    datasets = json.loads(content[0]["text"])
    assert isinstance(datasets, list)
    assert len(datasets) > 0

    # Check that the dataset has the enhanced properties
    dataset = datasets[0]
    assert "id" in dataset
    assert "name" in dataset
    assert "description" in dataset
    assert "document_count" in dataset
    assert "chunk_count" in dataset
    assert "embedding_count" in dataset
    assert "tree_count" in dataset
    assert "created_at" in dataset
    assert "last_updated" in dataset
    assert "status" in dataset
    assert "total_tokens" in dataset
    assert "embedding_models" in dataset
    assert "processing_status" in dataset


if __name__ == "__main__":
    pytest.main([__file__])
