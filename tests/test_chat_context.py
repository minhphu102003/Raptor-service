"""
Test cases for chat context functionality
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import ChatMessageORM, ChatSessionORM, MessageRole
from services.retrieval.answer_service import AnswerService


class TestAnswerService:
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def answer_service(self):
        """Create an AnswerService instance with mocked dependencies"""
        retrieval_svc = MagicMock()
        model_registry = MagicMock()
        return AnswerService(retrieval_svc=retrieval_svc, model_registry=model_registry)

    @pytest.mark.asyncio
    async def test_get_session_context(self, answer_service, mock_session):
        """Test getting session context"""
        # Mock chat session
        mock_session_obj = MagicMock(spec=ChatSessionORM)
        mock_session_obj.dataset_id = "test-dataset"
        mock_session_obj.assistant_id = "test-assistant"
        mock_session_obj.message_count = 3
        mock_session_obj.system_prompt = "You are a helpful assistant"
        mock_session_obj.assistant_config = {"model": "test-model"}

        # Mock chat messages
        mock_message1 = MagicMock(spec=ChatMessageORM)
        mock_message1.role = MessageRole.user
        mock_message1.content = "Hello"
        mock_message1.created_at = datetime(2023, 1, 1, 0, 0, 0)

        mock_message2 = MagicMock(spec=ChatMessageORM)
        mock_message2.role = MessageRole.assistant
        mock_message2.content = "Hi there!"
        mock_message2.created_at = datetime(2023, 1, 1, 0, 1, 0)

        # Setup mock returns
        answer_service.get_chat_session = AsyncMock(return_value=mock_session_obj)
        answer_service.get_chat_history = AsyncMock(return_value=[mock_message1, mock_message2])

        # Test the method
        context = await answer_service.get_session_context(mock_session, "test-session")

        # Verify results
        assert context["session_id"] == "test-session"
        assert context["dataset_id"] == "test-dataset"
        assert context["assistant_id"] == "test-assistant"
        assert context["message_count"] == 3
        assert len(context["recent_messages"]) == 2
        assert context["recent_messages"][0]["role"] == "user"
        assert context["recent_messages"][1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_summarize_conversation_context(self, answer_service, mock_session):
        """Test summarizing conversation context"""
        # Mock context data
        mock_context = {
            "session_id": "test-session",
            "dataset_id": "test-dataset",
            "assistant_id": "test-assistant",
            "message_count": 5,
            "recent_messages": [
                {"role": "user", "content": "What is Python?", "timestamp": "2023-01-01T00:00:00"},
                {
                    "role": "assistant",
                    "content": "Python is a programming language",
                    "timestamp": "2023-01-01T00:01:00",
                },
                {
                    "role": "user",
                    "content": "How do I install it?",
                    "timestamp": "2023-01-01T00:02:00",
                },
            ],
            "system_prompt": "You are a helpful assistant",
            "assistant_config": {"model": "test-model"},
        }

        # Mock the get_session_context method
        answer_service.get_session_context = AsyncMock(return_value=mock_context)

        # Test the method
        summary = await answer_service.summarize_conversation_context(
            mock_session, "test-session", 10
        )

        # Verify results
        assert summary["session_id"] == "test-session"
        assert summary["message_count"] == 5
        assert summary["recent_message_count"] == 3
        assert len(summary["topics_discussed"]) > 0
        assert summary["model_used"] == "test-model"
        assert summary["conversation_length"] == "short"
