from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant import AssistantORM
from db.models.chat import ChatMessageORM, ChatSessionORM, ChatSessionStatus, MessageRole


class ChatService:
    """Service for managing chat sessions and messages"""

    async def create_session(
        self,
        db_session: AsyncSession,
        dataset_id: str,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new chat session"""

        session_id = str(uuid4())

        # If assistant_id is provided, get the assistant config from the assistant
        if assistant_id and not assistant_config:
            result = await db_session.execute(
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
            system_prompt="You are a helpful assistant with access to a knowledge base.",
            message_count=0,
        )

        db_session.add(chat_session)
        await db_session.commit()
        await db_session.refresh(chat_session)

        return {
            "session_id": chat_session.session_id,
            "title": chat_session.title,
            "dataset_id": chat_session.dataset_id,
            "assistant_id": chat_session.assistant_id,
            "status": chat_session.status.value,
            "assistant_config": chat_session.assistant_config,
            "created_at": chat_session.created_at,
            "message_count": chat_session.message_count,
        }

    async def get_session(
        self, db_session: AsyncSession, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""

        result = await db_session.execute(
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

        return {
            "session_id": session.session_id,
            "title": session.title,
            "dataset_id": session.dataset_id,
            "assistant_id": session.assistant_id,
            "status": session.status.value,
            "assistant_config": session.assistant_config,
            "system_prompt": session.system_prompt,
            "message_count": session.message_count,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    async def list_sessions(
        self,
        db_session: AsyncSession,
        user_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List chat sessions with optional filtering"""

        query = select(ChatSessionORM).where(ChatSessionORM.status == ChatSessionStatus.active)

        if user_id:
            query = query.where(ChatSessionORM.user_id == user_id)
        if dataset_id:
            query = query.where(ChatSessionORM.dataset_id == dataset_id)
        if assistant_id:
            query = query.where(ChatSessionORM.assistant_id == assistant_id)

        query = query.order_by(desc(ChatSessionORM.updated_at)).limit(limit).offset(offset)

        result = await db_session.execute(query)
        sessions = result.scalars().all()

        return [
            {
                "session_id": session.session_id,
                "title": session.title,
                "dataset_id": session.dataset_id,
                "assistant_id": session.assistant_id,
                "message_count": session.message_count,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            }
            for session in sessions
        ]

    async def update_session(
        self,
        db_session: AsyncSession,
        session_id: str,
        title: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a chat session"""

        result = await db_session.execute(
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

        await db_session.commit()
        await db_session.refresh(session)

        return {
            "session_id": session.session_id,
            "title": session.title,
            "dataset_id": session.dataset_id,
            "assistant_id": session.assistant_id,
            "assistant_config": session.assistant_config,
            "updated_at": session.updated_at,
        }

    async def delete_session(self, db_session: AsyncSession, session_id: str) -> bool:
        """Delete (archive) a chat session"""

        result = await db_session.execute(
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
        await db_session.commit()
        return True

    async def get_messages(
        self, db_session: AsyncSession, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from a chat session"""

        result = await db_session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at)
            .limit(limit)
            .offset(offset)
        )

        messages = result.scalars().all()

        return [
            {
                "message_id": msg.message_id,
                "role": msg.role.value,
                "content": msg.content,
                "context_passages": msg.context_passages,
                "model_used": msg.model_used,
                "processing_time_ms": msg.processing_time_ms,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]
