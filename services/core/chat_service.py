from typing import Any, Dict, List, Optional

from db.models.chat import ChatMessageORM, ChatSessionORM
from repositories.chat_repo import ChatRepo


class ChatService:
    """Service for managing chat sessions and messages"""

    async def create_session(
        self,
        db_session,
        dataset_id: str,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        repo = ChatRepo(db_session)
        chat_session = await repo.create_session(
            dataset_id=dataset_id,
            title=title,
            user_id=user_id,
            assistant_id=assistant_id,
            assistant_config=assistant_config,
        )

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

    async def get_session(self, db_session, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        repo = ChatRepo(db_session)
        session = await repo.get_session(session_id)

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
        db_session,
        user_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List chat sessions with optional filtering"""
        repo = ChatRepo(db_session)
        sessions = await repo.list_sessions(
            user_id=user_id,
            dataset_id=dataset_id,
            assistant_id=assistant_id,
            limit=limit,
            offset=offset,
        )

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
        db_session,
        session_id: str,
        title: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a chat session"""
        repo = ChatRepo(db_session)
        session = await repo.update_session(
            session_id=session_id,
            title=title,
            assistant_config=assistant_config,
        )

        if not session:
            return None

        return {
            "session_id": session.session_id,
            "title": session.title,
            "dataset_id": session.dataset_id,
            "assistant_id": session.assistant_id,
            "assistant_config": session.assistant_config,
            "updated_at": session.updated_at,
        }

    async def delete_session(self, db_session, session_id: str) -> bool:
        """Delete (archive) a chat session"""
        repo = ChatRepo(db_session)
        return await repo.delete_session(session_id)

    async def get_messages(
        self, db_session, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from a chat session"""
        repo = ChatRepo(db_session)
        messages = await repo.get_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

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
