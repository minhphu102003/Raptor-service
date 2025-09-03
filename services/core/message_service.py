import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import (
    ChatMessageORM,
    ChatSessionORM,
    ChatSessionStatus,
    MessageRole,
)


class MessageService:
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

    async def get_chat_history(
        self, session: AsyncSession, session_id: str, limit: int = 50
    ) -> List[ChatMessageORM]:
        result = await session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def save_message(
        self,
        session: AsyncSession,
        session_id: str,
        role: MessageRole,
        content: str,
        context_passages: Optional[List[dict]] = None,
        retrieval_query: Optional[str] = None,
        model_used: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
    ) -> ChatMessageORM:
        message = ChatMessageORM(
            message_id=str(uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            context_passages=context_passages,
            retrieval_query=retrieval_query,
            model_used=model_used,
            generation_params=generation_params,
            processing_time_ms=processing_time_ms,
        )

        session.add(message)

        result = await session.execute(
            select(ChatSessionORM).where(ChatSessionORM.session_id == session_id)
        )
        chat_session = result.scalar_one_or_none()
        if chat_session:
            chat_session.message_count += 1

        await session.commit()
        return message
