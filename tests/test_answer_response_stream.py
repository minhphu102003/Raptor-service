import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.responses import StreamingResponse
import pytest

from services.retrieval.response_service import ResponseService
from services.retrieval.retrieval_service import RetrieveBody


@pytest.mark.asyncio
async def test_answer_with_context_streaming():
    """Test answer_with_context method with streaming enabled"""
    # Create mock services
    mock_retrieval_svc = AsyncMock()
    mock_model_registry = MagicMock()
    mock_message_service = AsyncMock()
    mock_prompt_service = AsyncMock()

    # Create ResponseService instance
    response_service = ResponseService(
        retrieval_svc=mock_retrieval_svc,
        model_registry=mock_model_registry,
        message_service=mock_message_service,
        prompt_service=mock_prompt_service,
    )

    # Mock the retrieval service to return sample data
    mock_retrieval_svc.retrieve.return_value = {
        "code": 200,
        "data": [
            {"text": "This is a sample passage 1", "score": 0.9},
            {"text": "This is a sample passage 2", "score": 0.8},
        ],
    }

    # Mock the prompt service
    mock_prompt_service.build_prompt.return_value = "Generated prompt"

    # Mock the model registry and client
    mock_client = AsyncMock()
    mock_model_registry.get_client.return_value = mock_client

    # Mock the streaming response
    async def mock_astream(prompt, temperature, max_tokens):
        yield "First chunk"
        yield "Second chunk"
        yield "Final chunk"

    mock_client.astream = mock_astream

    # Create a RetrieveBody
    body = RetrieveBody(
        dataset_id="test_dataset", query="Test query", mode="collapsed", top_k=5, expand_k=3
    )

    # Create mock repo and db_session
    mock_repo = MagicMock()
    mock_db_session = AsyncMock()

    # Call the method with streaming enabled
    result = await response_service.answer_with_context(
        body, repo=mock_repo, db_session=mock_db_session, stream=True
    )

    # Verify it returns a StreamingResponse
    assert isinstance(result, StreamingResponse)

    # Collect the streamed response
    chunks = []
    async for chunk in result.body_iterator:
        chunks.append(chunk)

    # Verify we got the expected chunks
    assert len(chunks) == 3
    assert "".join(chunks) == "First chunkSecond chunkFinal chunk"

    # Verify the retrieval service was called
    mock_retrieval_svc.retrieve.assert_called_once_with(body, repo=mock_repo)

    # Verify the prompt service was called
    mock_prompt_service.build_prompt.assert_called_once()

    # Verify the model registry was called
    mock_model_registry.get_client.assert_called_once()


@pytest.mark.asyncio
async def test_answer_with_context_non_streaming():
    """Test answer_with_context method with streaming disabled"""
    # Create mock services
    mock_retrieval_svc = AsyncMock()
    mock_model_registry = MagicMock()
    mock_message_service = AsyncMock()
    mock_prompt_service = AsyncMock()

    # Create ResponseService instance
    response_service = ResponseService(
        retrieval_svc=mock_retrieval_svc,
        model_registry=mock_model_registry,
        message_service=mock_message_service,
        prompt_service=mock_prompt_service,
    )

    # Mock the retrieval service to return sample data
    mock_retrieval_svc.retrieve.return_value = {
        "code": 200,
        "data": [
            {"text": "This is a sample passage 1", "score": 0.9},
            {"text": "This is a sample passage 2", "score": 0.8},
        ],
    }

    # Mock the prompt service
    mock_prompt_service.build_prompt.return_value = "Generated prompt"

    # Mock the model registry and client
    mock_client = AsyncMock()
    mock_model_registry.get_client.return_value = mock_client
    mock_client.generate.return_value = "This is a complete answer"

    # Create a RetrieveBody
    body = RetrieveBody(
        dataset_id="test_dataset", query="Test query", mode="collapsed", top_k=5, expand_k=3
    )

    # Create mock repo and db_session
    mock_repo = MagicMock()
    mock_db_session = AsyncMock()

    # Call the method with streaming disabled
    result = await response_service.answer_with_context(
        body, repo=mock_repo, db_session=mock_db_session, stream=False
    )

    # Verify it returns a dictionary
    assert isinstance(result, dict)
    assert "answer" in result
    assert result["answer"] == "This is a complete answer"

    # Verify the retrieval service was called
    mock_retrieval_svc.retrieve.assert_called_once_with(body, repo=mock_repo)

    # Verify the prompt service was called
    mock_prompt_service.build_prompt.assert_called_once()

    # Verify the model client was called
    mock_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_answer_streaming():
    """Test answer method with streaming enabled"""
    # Create mock services
    mock_retrieval_svc = AsyncMock()
    mock_model_registry = MagicMock()
    mock_message_service = AsyncMock()
    mock_prompt_service = AsyncMock()

    # Create ResponseService instance
    response_service = ResponseService(
        retrieval_svc=mock_retrieval_svc,
        model_registry=mock_model_registry,
        message_service=mock_message_service,
        prompt_service=mock_prompt_service,
    )

    # Create a mock body with stream=True
    mock_body = MagicMock()
    mock_body.query = "Test query"
    mock_body.answer_model = "DeepSeek-V3"
    mock_body.temperature = 0.7
    mock_body.max_tokens = 4000
    mock_body.stream = True
    mock_body.top_k = 5
    mock_body.mode = "collapsed"

    # Mock the retrieval service to return sample data
    mock_retrieval_svc.retrieve.return_value = {
        "code": 200,
        "data": [
            {"text": "This is a sample passage 1", "score": 0.9},
            {"text": "This is a sample passage 2", "score": 0.8},
        ],
    }

    # Mock the prompt service
    mock_prompt_service.build_prompt.return_value = "Generated prompt"

    # Mock the model registry and client
    mock_client = AsyncMock()
    mock_model_registry.get_client.return_value = mock_client

    # Mock the streaming response
    async def mock_astream(prompt, temperature, max_tokens):
        yield "First chunk"
        yield "Second chunk"
        yield "Final chunk"

    mock_client.astream = mock_astream

    # Create mock repo
    mock_repo = MagicMock()

    # Call the method with streaming enabled
    result = await response_service.answer(mock_body, mock_repo)

    # Verify it returns a StreamingResponse
    assert isinstance(result, StreamingResponse)

    # Collect the streamed response
    chunks = []
    async for chunk in result.body_iterator:
        chunks.append(chunk)

    # Verify we got the expected chunks
    assert len(chunks) == 3
    assert "".join(chunks) == "First chunkSecond chunkFinal chunk"


@pytest.mark.asyncio
async def test_answer_non_streaming():
    """Test answer method with streaming disabled"""
    # Create mock services
    mock_retrieval_svc = AsyncMock()
    mock_model_registry = MagicMock()
    mock_message_service = AsyncMock()
    mock_prompt_service = AsyncMock()

    # Create ResponseService instance
    response_service = ResponseService(
        retrieval_svc=mock_retrieval_svc,
        model_registry=mock_model_registry,
        message_service=mock_message_service,
        prompt_service=mock_prompt_service,
    )

    # Create a mock body with stream=False
    mock_body = MagicMock()
    mock_body.query = "Test query"
    mock_body.answer_model = "DeepSeek-V3"
    mock_body.temperature = 0.7
    mock_body.max_tokens = 4000
    mock_body.stream = False
    mock_body.top_k = 5
    mock_body.mode = "collapsed"

    # Mock the retrieval service to return sample data
    mock_retrieval_svc.retrieve.return_value = {
        "code": 200,
        "data": [
            {"text": "This is a sample passage 1", "score": 0.9},
            {"text": "This is a sample passage 2", "score": 0.8},
        ],
    }

    # Mock the prompt service
    mock_prompt_service.build_prompt.return_value = "Generated prompt"

    # Mock the model registry and client
    mock_client = AsyncMock()
    mock_model_registry.get_client.return_value = mock_client
    mock_client.generate.return_value = "This is a complete answer"

    # Create mock repo
    mock_repo = MagicMock()

    # Call the method with streaming disabled
    result = await response_service.answer(mock_body, mock_repo)

    # Verify it returns a dictionary
    assert isinstance(result, dict)
    assert "answer" in result
    assert result["answer"] == "This is a complete answer"
