import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_local.tools.rag_summarize import rag_summarize


@pytest.mark.asyncio
async def test_rag_summarize_with_container():
    """Test rag_summarize with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return specific data
    mock_node_data = [
        {"node_id": "node_1", "text": "This is the text content of node 1."},
        {"node_id": "node_2", "text": "This is the text content of node 2."},
    ]
    mock_repo.get_node_texts_by_ids.return_value = mock_node_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Patch the summarizer in the rag_summarize function
    import mcp_local.tools.rag_summarize as rag_summarize_module

    original_llm_summarizer = rag_summarize_module.LLMSummarizer
    original_make_llm = rag_summarize_module.make_llm
    original_get_service_config = rag_summarize_module.get_service_config

    mock_llm_summarizer = MagicMock()
    mock_llm = AsyncMock()
    mock_config = MagicMock()

    # Mock the service config
    mock_service_config = MagicMock()
    mock_service_config.model_config = mock_config
    mock_config.get_default_model.return_value = "test_model"

    rag_summarize_module.get_service_config = lambda: mock_service_config
    rag_summarize_module.make_llm = lambda model, config: mock_llm

    # Mock the summarizer
    mock_llm_summarizer_instance = AsyncMock()
    mock_llm_summarizer_instance.summarize_cluster = AsyncMock(return_value="Test summary")
    rag_summarize_module.LLMSummarizer = lambda llm, config: mock_llm_summarizer_instance

    try:
        # Call the function
        result = await rag_summarize(["node_1", "node_2"], container=mock_container)

        # Verify the result
        assert not result["isError"]
        assert "content" in result
        assert len(result["content"]) > 0

        # Verify the mock was called correctly
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
        mock_repo.get_node_texts_by_ids.assert_called_once_with(node_ids=["node_1", "node_2"])
    finally:
        # Restore original classes
        rag_summarize_module.LLMSummarizer = original_llm_summarizer
        rag_summarize_module.make_llm = original_make_llm
        rag_summarize_module.get_service_config = original_get_service_config


@pytest.mark.asyncio
async def test_rag_summarize_without_container():
    """Test rag_summarize without container (backward compatibility)"""
    # Call the function without container
    result = await rag_summarize(["node_1", "node_2"], container=None)

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "combined summary of nodes" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_summarize_with_container_no_nodes_found():
    """Test rag_summarize with container when no nodes are found"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return no data
    mock_repo.get_node_texts_by_ids.return_value = []

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_summarize(["node_1", "node_2"], container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "No nodes found to summarize" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_summarize_with_container_no_text_content():
    """Test rag_summarize with container when nodes have no text content"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock repo to return nodes with no text
    mock_node_data = [{"node_id": "node_1", "text": None}, {"node_id": "node_2", "text": ""}]
    mock_repo.get_node_texts_by_ids.return_value = mock_node_data

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Call the function
    result = await rag_summarize(["node_1", "node_2"], container=mock_container)

    # Verify the result
    assert not result["isError"]
    assert "No text content found" in result["content"][0]["text"]
