from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import ChatContextORM, ChatMessageORM, ChatSessionORM


class ChatContextRepo:
    """Repository for chat context operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_session_context_messages(
        self, session_id: str, limit: int = 50
    ) -> List[ChatMessageORM]:
        """Get chat message history for a session"""
        result = await self.session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages

    async def get_session_with_details(self, session_id: str) -> Optional[ChatSessionORM]:
        """Get chat session with all details"""
        result = await self.session.execute(
            select(ChatSessionORM).where(ChatSessionORM.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def delete_old_messages(self, session_id: str, keep_last: int = 2) -> int:
        """Delete old messages, keeping only the last N messages"""
        # First get all message IDs ordered by creation time
        result = await self.session.execute(
            select(ChatMessageORM.message_id)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at)
        )
        message_ids = [row[0] for row in result.all()]

        # If we have more messages than we want to keep, delete the older ones
        if len(message_ids) > keep_last:
            ids_to_delete = message_ids[:-keep_last]  # All except the last keep_last
            if ids_to_delete:
                delete_stmt = delete(ChatMessageORM).where(
                    ChatMessageORM.message_id.in_(ids_to_delete)
                )
                await self.session.execute(delete_stmt)

                # Update session message count
                session_result = await self.session.execute(
                    select(ChatSessionORM).where(ChatSessionORM.session_id == session_id)
                )
                chat_session = session_result.scalar_one_or_none()
                if chat_session:
                    chat_session.message_count = keep_last
                    await self.session.commit()

                return len(ids_to_delete)

        return 0

    async def get_or_create_context(self, session_id: str) -> ChatContextORM:
        """Get existing context or create a new one"""
        result = await self.session.execute(
            select(ChatContextORM).where(ChatContextORM.session_id == session_id)
        )
        context = result.scalar_one_or_none()

        if not context:
            context = ChatContextORM(
                context_id=f"context_{session_id}",
                session_id=session_id,
                context_messages=[],
                context_size_tokens=0,
                max_context_tokens=4000,
                last_message_id="",
            )
            self.session.add(context)

        return context

    async def update_context(
        self,
        context: ChatContextORM,
        messages: List[Dict[str, Any]],
        total_tokens: int,
        last_message_id: str,
    ) -> None:
        """Update context with new messages and token count"""
        context.context_messages = messages
        context.context_size_tokens = total_tokens
        context.last_message_id = last_message_id
        await self.session.commit()
