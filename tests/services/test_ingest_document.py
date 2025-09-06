import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.base_tools import ingest_document


@pytest.mark.asyncio
async def test_ingest_document_with_container():
    """Test ingest_document with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_document_service = AsyncMock()

    # Configure container to return mock components
    mock_container.make_document_service.return_value = mock_document_service

    # Configure mock document service to return specific data
    mock_result = {
        "data": {
            "doc_id": "doc_123",
            "chunks": 5,
        }
    }
    mock_document_service.ingest_markdown.return_value = mock_result

    # Call the function
    result = await ingest_document(
        dataset_id="test_dataset",
        file_content="This is a test document content.",
        source="test_source",
        tags=["tag1", "tag2"],
        container=mock_container,
    )

    # Verify the result
    assert not result["isError"]
    assert "Successfully ingested document" in result["content"][0]["text"]
    assert "doc_123" in result["content"][0]["text"]
    assert "5" in result["content"][0]["text"]

    # Verify the mock was called correctly
    mock_container.make_document_service.assert_called_once()
    mock_document_service.ingest_markdown.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_document_without_container():
    """Test ingest_document without container (backward compatibility)"""
    # Call the function without container
    result = await ingest_document(
        dataset_id="test_dataset",
        file_content="This is a test document content.",
        source="test_source",
        tags=["tag1", "tag2"],
        container=None,
    )

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "Successfully ingested document" in result["content"][0]["text"]
    assert "test_dataset" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_ingest_document_database_error():
    """Test ingest_document when database error occurs"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_document_service = AsyncMock()

    # Configure container to return mock components
    mock_container.make_document_service.return_value = mock_document_service

    # Configure mock document service to raise an exception
    mock_document_service.ingest_markdown.side_effect = Exception("Database error")

    # Call the function
    result = await ingest_document(
        dataset_id="test_dataset",
        file_content="This is a test document content.",
        source="test_source",
        tags=["tag1", "tag2"],
        container=mock_container,
    )

    # Verify the result is an error
    assert result["isError"]
    assert "Failed to ingest document" in str(result["content"][0]["text"])
