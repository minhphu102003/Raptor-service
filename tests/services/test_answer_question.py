import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_local.tools.document_tools import answer_question


@pytest.mark.asyncio
async def test_answer_question_with_container():
    """Test answer_question with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()
    mock_retrieval_svc = AsyncMock()
    mock_fpt_client = AsyncMock()
    mock_voyage_client = AsyncMock()
    mock_rewrite_svc = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock retrieval service to return specific data
    mock_retrieval_result = {
        "code": 200,
        "data": [
            {
                "chunk_id": "chunk_1",
                "doc_id": "doc_1",
                "text": "This is relevant content for the question.",
                "score": 0.85,
            }
        ],
    }
    mock_retrieval_svc.retrieve.return_value = mock_retrieval_result

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Mock the FPT client to return a specific answer
    mock_fpt_client.generate = AsyncMock(
        return_value="This is a generated answer based on the retrieved context."
    )

    # Patch the services in the answer_question function
    import mcp_local.tools.document_tools as document_tools_module

    original_fpt_client = document_tools_module.FPTLLMClient
    original_voyage_client = document_tools_module.VoyageEmbeddingClientAsync
    original_rewrite_svc = document_tools_module.QueryRewriteService
    original_retrieval_svc = document_tools_module.RetrievalService

    document_tools_module.FPTLLMClient = lambda **kwargs: mock_fpt_client
    document_tools_module.VoyageEmbeddingClientAsync = lambda **kwargs: mock_voyage_client
    document_tools_module.QueryRewriteService = lambda **kwargs: mock_rewrite_svc
    document_tools_module.RetrievalService = lambda **kwargs: mock_retrieval_svc

    try:
        # Call the function
        result = await answer_question(
            "test_dataset", "What is this about?", "collapsed", 5, 0.7, container=mock_container
        )

        # Verify the result
        assert not result["isError"]
        assert "content" in result
        assert len(result["content"]) > 0
        assert "Answer:" in result["content"][0]["text"]
        assert "This is a generated answer" in result["content"][0]["text"]

        # Verify the mock was called correctly
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    finally:
        # Restore original classes
        document_tools_module.FPTLLMClient = original_fpt_client
        document_tools_module.VoyageEmbeddingClientAsync = original_voyage_client
        document_tools_module.QueryRewriteService = original_rewrite_svc
        document_tools_module.RetrievalService = original_retrieval_svc


@pytest.mark.asyncio
async def test_answer_question_without_container():
    """Test answer_question without container (backward compatibility)"""
    # Call the function without container
    result = await answer_question(
        "test_dataset", "What is this about?", "collapsed", 5, 0.7, container=None
    )

    # Verify the result (should use simulated data)
    assert not result["isError"]
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Answer:" in result["content"][0]["text"]
    assert "comprehensive response" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_answer_question_retrieval_failure():
    """Test answer_question when retrieval fails"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()
    mock_retrieval_svc = AsyncMock()

    # Configure container to return mock components
    mock_container.make_uow.return_value = mock_uow
    mock_container.make_retrieval_repo.return_value = mock_repo

    # Configure mock retrieval service to return an error
    mock_retrieval_result = {"code": 500, "message": "Retrieval failed"}
    mock_retrieval_svc.retrieve.return_value = mock_retrieval_result

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Mock the services in the answer_question function
    import mcp_local.tools.document_tools as document_tools_module

    original_fpt_client = document_tools_module.FPTLLMClient
    original_voyage_client = document_tools_module.VoyageEmbeddingClientAsync
    original_rewrite_svc = document_tools_module.QueryRewriteService
    original_retrieval_svc = document_tools_module.RetrievalService

    mock_fpt_client = AsyncMock()
    mock_voyage_client = AsyncMock()
    mock_rewrite_svc = AsyncMock()

    document_tools_module.FPTLLMClient = lambda **kwargs: mock_fpt_client
    document_tools_module.VoyageEmbeddingClientAsync = lambda **kwargs: mock_voyage_client
    document_tools_module.QueryRewriteService = lambda **kwargs: mock_rewrite_svc
    document_tools_module.RetrievalService = lambda **kwargs: mock_retrieval_svc

    try:
        # Call the function
        result = await answer_question(
            "test_dataset", "What is this about?", "collapsed", 5, 0.7, container=mock_container
        )

        # Verify the result is an error
        assert result["isError"]
        assert "Failed to generate answer" in result["content"][0]["text"]
    finally:
        # Restore original classes
        document_tools_module.FPTLLMClient = original_fpt_client
        document_tools_module.VoyageEmbeddingClientAsync = original_voyage_client
        document_tools_module.QueryRewriteService = original_rewrite_svc
        document_tools_module.RetrievalService = original_retrieval_svc
