from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.chat_context_repo import ChatContextRepo
from services.retrieval.answer_service import AnswerService


class ChatContextService:
    """Service for managing chat context operations"""

    def __init__(self, answer_service: AnswerService):
        self.answer_service = answer_service

    async def get_session_context(self, session: AsyncSession, session_id: str) -> Dict[str, Any]:
        """Get session context including chat history and associated information."""
        repo = ChatContextRepo(session)
        context = await self.answer_service.get_session_context(session, session_id)
        return context

    async def get_session_context_summary(
        self, session: AsyncSession, session_id: str, max_messages: int = 10
    ) -> Dict[str, Any]:
        """Get a summary of session context including recent messages and metadata."""
        context = await self.answer_service.get_session_context(session, session_id, max_messages)

        if "error" in context:
            return context

        # Create a summary of the context
        summary = {
            "session_id": context["session_id"],
            "dataset_id": context["dataset_id"],
            "assistant_id": context["assistant_id"],
            "message_count": context["message_count"],
            "recent_message_count": len(context["recent_messages"]),
            "system_prompt": context["system_prompt"],
        }

        # Handle model_info with proper error handling
        try:
            assistant_config = context.get("assistant_config")
            if isinstance(assistant_config, dict):
                summary["model_info"] = assistant_config.get("model")
            else:
                summary["model_info"] = None
        except (KeyError, TypeError):
            summary["model_info"] = None

        # Handle last_message_timestamp with proper error handling
        try:
            recent_messages = context.get("recent_messages")
            if isinstance(recent_messages, list) and len(recent_messages) > 0:
                last_message = recent_messages[-1]
                if isinstance(last_message, dict) and "timestamp" in last_message:
                    summary["last_message_timestamp"] = last_message["timestamp"]
                else:
                    summary["last_message_timestamp"] = None
            else:
                summary["last_message_timestamp"] = None
        except (KeyError, TypeError, IndexError):
            summary["last_message_timestamp"] = None

        return summary

    async def get_conversation_summary(
        self, session: AsyncSession, session_id: str, max_messages: int = 10
    ) -> Dict[str, Any]:
        """Get a summary of the conversation including topics and key information."""
        summary = await self.answer_service.summarize_conversation_context(
            session, session_id, max_messages
        )
        return summary

    async def clear_session_context(self, session: AsyncSession, session_id: str) -> Dict[str, Any]:
        """Clear session context by deleting old messages (keeping last 2 messages)."""
        repo = ChatContextRepo(session)

        # First verify session exists
        chat_session = await repo.get_session_with_details(session_id)
        if not chat_session:
            return {"error": "Chat session not found"}

        # Delete old messages, keeping last 2
        deleted_count = await repo.delete_old_messages(session_id, keep_last=2)

        if deleted_count > 0:
            return {
                "message": f"Deleted {deleted_count} old messages. Kept last 2 messages.",
            }
        else:
            return {
                "message": "Not enough messages to clear context. Session has 2 or fewer messages.",
            }
