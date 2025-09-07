import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_local.tools.base_tools import list_datasets


@pytest.mark.asyncio
async def test_list_datasets_with_container():
    """Test list_datasets with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_dataset_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_dataset_repo.return_value = mock_dataset_repo

    # Configure mock dataset repo to return specific data
    mock_datasets = [
        {
            "id": "ds_test1",
            "name": "Test Dataset 1",
            "description": "Test dataset for unit testing",
            "document_count": 3,
            "created_at": "2023-01-01T00:00:00Z",
        },
        {
            "id": "ds_test2",
            "name": "Test Dataset 2",
            "description": "Another test dataset",
            "document_count": 7,
            "created_at": "2023-01-02T00:00:00Z",
        },
    ]
    mock_dataset_repo.list_datasets.return_value = mock_datasets

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await list_datasets(container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Available datasets" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_uow.assert_called_once()
    mock_container.make_dataset_repo.assert_called_once_with(mock_uow)
    mock_dataset_repo.list_datasets.assert_called_once()


@pytest.mark.asyncio
async def test_list_datasets_without_container():
    """Test list_datasets without container (backward compatibility)"""
    # Call the function without container
    result = await list_datasets(container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Available datasets" in result["content"][0]["text"]
    assert "ds_demo" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_list_datasets_database_error():
    """Test list_datasets when database error occurs"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_dataset_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_dataset_repo.return_value = mock_dataset_repo

    # Configure mock dataset repo to raise an exception
    mock_dataset_repo.list_datasets.side_effect = Exception("Database connection failed")

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await list_datasets(container=mock_container)

    # Verify the result is an error
    assert result["isError"]
    assert "Failed to list datasets" in result["content"][0]["text"]
