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
from services.retrieval.retrieval_service import RetrievalService, RetrieveBody


class ChatSessionService:
    def __init__(self, *, retrieval_svc: RetrievalService, model_registry):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry

    async def create_chat_session(
        self,
        session: AsyncSession,
        dataset_id: str,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> ChatSessionORM:
        session_id = str(uuid4())

        if assistant_id and not assistant_config:
            result = await session.execute(
                select(AssistantORM).where(AssistantORM.assistant_id == assistant_id)
            )
            assistant = result.scalar_one_or_none()
            if assistant:
                assistant_config = assistant.model_settings

        chat_session = ChatSessionORM(
            session_id=session_id,
            user_id=user_id,
            assistant_id=assistant_id,
            dataset_id=dataset_id,
            title=title,
            status=ChatSessionStatus.active,
            assistant_config=assistant_config
            or {"model": "DeepSeek-V3", "temperature": 0.7, "max_tokens": 4000},
            system_prompt=system_prompt or "You are a helpful assistant.",
            message_count=0,
        )

        session.add(chat_session)
        await session.commit()
        return chat_session

    async def get_chat_session(
        self, session: AsyncSession, session_id: str
    ) -> Optional[ChatSessionORM]:
        result = await session.execute(
            select(ChatSessionORM).where(
                and_(
                    ChatSessionORM.session_id == session_id,
                    ChatSessionORM.status == ChatSessionStatus.active,
                )
            )
        )
        return result.scalar_one_or_none()
