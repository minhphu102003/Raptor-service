import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.tools.rag_retrieve import rag_retrieve


@pytest.mark.asyncio
async def test_rag_retrieve_with_container():
    """Test rag_retrieve with container for database connectivity"""
    # Create mock container and its components
    mock_container = MagicMock()
    mock_uow = AsyncMock()
    mock_repo = AsyncMock()
    mock_retrieval_svc = AsyncMock()

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
                "text": "This is relevant content for the query.",
                "dist": 0.85,
            }
        ],
    }
    mock_retrieval_svc.retrieve.return_value = mock_retrieval_result

    # Mock the context manager behavior
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    # Patch the services in the rag_retrieve function
    import mcp.tools.rag_retrieve as rag_retrieve_module
    import services as services_module
    import services.embedding.embedding_query_service as embedding_service_module

    original_fpt_client = services_module.FPTLLMClient
    original_voyage_client = services_module.VoyageEmbeddingClientAsync
    original_rewrite_svc = services_module.QueryRewriteService
    original_retrieval_svc = services_module.RetrievalService
    original_embedding_service = embedding_service_module.EmbeddingService

    mock_fpt_client = AsyncMock()
    mock_voyage_client = AsyncMock()
    mock_rewrite_svc = AsyncMock()
    mock_embedding_service = AsyncMock()

    # Mock the embed_query method that's being called
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

    services_module.FPTLLMClient = lambda **kwargs: mock_fpt_client
    services_module.VoyageEmbeddingClientAsync = lambda **kwargs: mock_voyage_client
    services_module.QueryRewriteService = lambda **kwargs: mock_rewrite_svc
    services_module.RetrievalService = lambda **kwargs: mock_retrieval_svc
    embedding_service_module.EmbeddingService = lambda **kwargs: mock_embedding_service

    try:
        # Call the function
        result = await rag_retrieve(
            "test_dataset",
            "What is this about?",
            5,
            None,
            None,
            None,
            None,
            container=mock_container,
        )

        # Verify the result
        assert not result["isError"]
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "resource"

        # Verify the mock was called correctly
        mock_container.make_uow.assert_called_once()
        mock_container.make_retrieval_repo.assert_called_once_with(mock_uow)
    finally:
        # Restore original classes
        services_module.FPTLLMClient = original_fpt_client
        services_module.VoyageEmbeddingClientAsync = original_voyage_client
        services_module.QueryRewriteService = original_rewrite_svc
        services_module.RetrievalService = original_retrieval_svc
        embedding_service_module.EmbeddingService = original_embedding_service


@pytest.mark.asyncio
async def test_rag_retrieve_without_container():
    """Test rag_retrieve without container (should raise error)"""
    # Call the function without container - should raise an error
    result = await rag_retrieve(
        "test_dataset", "What is this about?", 5, None, None, None, None, container=None
    )

    # Verify the result is an error
    assert result["isError"]
    assert "Container is required" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_rag_retrieve_retrieval_failure():
    """Test rag_retrieve when retrieval fails"""
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

    # Patch the services in the rag_retrieve function
    import mcp.tools.rag_retrieve as rag_retrieve_module
    import services as services_module
    import services.embedding.embedding_query_service as embedding_service_module

    original_fpt_client = services_module.FPTLLMClient
    original_voyage_client = services_module.VoyageEmbeddingClientAsync
    original_rewrite_svc = services_module.QueryRewriteService
    original_retrieval_svc = services_module.RetrievalService
    original_embedding_service = embedding_service_module.EmbeddingService

    mock_fpt_client = AsyncMock()
    mock_voyage_client = AsyncMock()
    mock_rewrite_svc = AsyncMock()
    mock_embedding_service = AsyncMock()

    # Mock the embed_query method that's being called
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

    services_module.FPTLLMClient = lambda **kwargs: mock_fpt_client
    services_module.VoyageEmbeddingClientAsync = lambda **kwargs: mock_voyage_client
    services_module.QueryRewriteService = lambda **kwargs: mock_rewrite_svc
    services_module.RetrievalService = lambda **kwargs: mock_retrieval_svc
    embedding_service_module.EmbeddingService = lambda **kwargs: mock_embedding_service

    try:
        # Call the function
        result = await rag_retrieve(
            "test_dataset",
            "What is this about?",
            5,
            None,
            None,
            None,
            None,
            container=mock_container,
        )

        # Verify the result is an error
        assert result["isError"]
        assert "Failed to retrieve documents" in result["content"][0]["text"]
    finally:
        # Restore original classes
        services_module.FPTLLMClient = original_fpt_client
        services_module.VoyageEmbeddingClientAsync = original_voyage_client
        services_module.QueryRewriteService = original_rewrite_svc
        services_module.RetrievalService = original_retrieval_svc
        embedding_service_module.EmbeddingService = original_embedding_service
