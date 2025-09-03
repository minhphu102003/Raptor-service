from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant import AssistantORM
from db.models.chat import ChatMessageORM, ChatSessionORM, ChatSessionStatus, MessageRole


class ChatRepo:
    """Repository for basic chat operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        dataset_id: str,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> ChatSessionORM:
        """Create a new chat session"""
        session_id = str(uuid4())

        # If assistant_id is provided, get the assistant config from the assistant
        if assistant_id and not assistant_config:
            result = await self.session.execute(
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
            or {
                "model": "DeepSeek-V3",
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_k": 5,
                "mode": "tree",
            },
            system_prompt=system_prompt
            or "You are a helpful assistant with access to a knowledge base.",
            message_count=0,
        )

        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        return chat_session

    async def get_session(self, session_id: str) -> Optional[ChatSessionORM]:
        """Get a chat session by ID"""
        result = await self.session.execute(
            select(ChatSessionORM).where(
                and_(
                    ChatSessionORM.session_id == session_id,
                    ChatSessionORM.status == ChatSessionStatus.active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatSessionORM]:
        """List chat sessions with optional filtering"""
        query = select(ChatSessionORM).where(ChatSessionORM.status == ChatSessionStatus.active)

        if user_id:
            query = query.where(ChatSessionORM.user_id == user_id)
        if dataset_id:
            query = query.where(ChatSessionORM.dataset_id == dataset_id)
        if assistant_id:
            query = query.where(ChatSessionORM.assistant_id == assistant_id)

        query = query.order_by(desc(ChatSessionORM.updated_at)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[ChatSessionORM]:
        """Update a chat session"""
        result = await self.session.execute(
            select(ChatSessionORM).where(
                and_(
                    ChatSessionORM.session_id == session_id,
                    ChatSessionORM.status == ChatSessionStatus.active,
                )
            )
        )

        session = result.scalar_one_or_none()
        if not session:
            return None

        if title is not None:
            session.title = title
        if assistant_config is not None:
            session.assistant_config = assistant_config

        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete (archive) a chat session"""
        result = await self.session.execute(
            select(ChatSessionORM).where(
                and_(
                    ChatSessionORM.session_id == session_id,
                    ChatSessionORM.status == ChatSessionStatus.active,
                )
            )
        )

        session = result.scalar_one_or_none()
        if not session:
            return False

        session.status = ChatSessionStatus.deleted
        await self.session.commit()
        return True

    async def get_messages(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[ChatMessageORM]:
        """Get messages from a chat session"""
        result = await self.session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at)
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def save_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        context_passages: Optional[List[dict]] = None,
        retrieval_query: Optional[str] = None,
        model_used: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
    ) -> ChatMessageORM:
        """Save a chat message to database"""
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

        self.session.add(message)

        # Update session message count
        chat_session = await self.get_session(session_id)
        if chat_session:
            chat_session.message_count += 1

        await self.session.commit()
        return message

    async def count_sessions(
        self,
        user_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
    ) -> int:
        """Count total chat sessions with optional filtering"""
        query = select(ChatSessionORM).where(ChatSessionORM.status == ChatSessionStatus.active)

        if user_id:
            query = query.where(ChatSessionORM.user_id == user_id)
        if dataset_id:
            query = query.where(ChatSessionORM.dataset_id == dataset_id)
        if assistant_id:
            query = query.where(ChatSessionORM.assistant_id == assistant_id)

        result = await self.session.execute(query)
        return len(list(result.scalars().all()))
