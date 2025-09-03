import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant import AssistantORM
from db.models.chat import (
    ChatMessageORM,
    ChatSessionORM,
    ChatSessionStatus,
    MessageRole,
)
from repositories.retrieval_repo import RetrievalRepo
from services.core.chat_session_service import ChatSessionService
from services.core.message_service import MessageService
from services.retrieval.prompt_service import PromptService
from services.retrieval.response_service import ResponseService
from services.retrieval.retrieval_service import RetrievalService, RetrieveBody


class AnswerService:
    def __init__(self, *, retrieval_svc: RetrievalService, model_registry):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry

        # Initialize the specialized services
        self.chat_session_service = ChatSessionService(
            retrieval_svc=retrieval_svc, model_registry=model_registry
        )
        self.message_service = MessageService()
        self.prompt_service = PromptService()
        self.response_service = ResponseService(
            retrieval_svc, model_registry, self.message_service, self.prompt_service
        )

    # Delegate methods to specialized services
    async def create_chat_session(self, *args, **kwargs):
        return await self.chat_session_service.create_chat_session(*args, **kwargs)

    async def get_chat_session(self, *args, **kwargs):
        return await self.chat_session_service.get_chat_session(*args, **kwargs)

    async def get_chat_history(self, *args, **kwargs):
        return await self.message_service.get_chat_history(*args, **kwargs)

    async def get_session_context(
        self, session: AsyncSession, session_id: str, max_context_messages: int = 6
    ):
        # This is a simplified implementation that would typically retrieve context from a repository
        chat_session = await self.get_chat_session(session, session_id)
        if not chat_session:
            return {"error": "Session not found"}

        recent_messages = await self.get_chat_history(session, session_id, max_context_messages)

        context_messages = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.created_at if msg.created_at else None,
            }
            for msg in recent_messages
        ]

        return {
            "session_id": session_id,
            "dataset_id": chat_session.dataset_id,
            "assistant_id": chat_session.assistant_id,
            "message_count": chat_session.message_count,
            "recent_messages": context_messages,
            "system_prompt": chat_session.system_prompt,
            "assistant_config": chat_session.assistant_config,
        }

    async def build_enhanced_context_prompt(self, *args, **kwargs):
        return await self.prompt_service.build_enhanced_context_prompt(*args, **kwargs)

    async def save_message(self, *args, **kwargs):
        return await self.message_service.save_message(*args, **kwargs)

    async def build_prompt(self, *args, **kwargs):
        return await self.prompt_service.build_prompt(*args, **kwargs)

    async def answer_with_context(self, *args, **kwargs):
        return await self.response_service.answer_with_context(*args, **kwargs)

    async def answer(self, *args, **kwargs):
        return await self.response_service.answer(*args, **kwargs)

    async def summarize_conversation_context(
        self, session: AsyncSession, session_id: str, max_messages: int = 10
    ):
        # This would typically retrieve context from a repository
        # For now, we'll return a placeholder
        return {
            "session_id": session_id,
            "message_count": 0,
            "recent_message_count": 0,
            "topics_discussed": [],
            "model_used": "unknown",
            "conversation_length": "short",
        }
