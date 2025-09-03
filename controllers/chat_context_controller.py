from fastapi import HTTPException, Request, status

from services import AnswerService, ChatContextService


class ChatContextController:
    """Controller for chat context HTTP endpoints"""

    def __init__(self, request: Request, answer_service: AnswerService):
        self.request = request
        self.container = request.app.state.container
        self._context_service = ChatContextService(answer_service)

    async def get_session_context(self, session_id: str):
        """Get session context including chat history and associated information."""
        uow = self.container.make_uow()
        async with uow:
            context = await self._context_service.get_session_context(uow.session, session_id)

            if "error" in context:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )

            return {"code": 200, "data": context}

    async def get_session_context_summary(self, session_id: str, max_messages: int = 10):
        """Get a summary of session context including recent messages and metadata."""
        uow = self.container.make_uow()
        async with uow:
            summary = await self._context_service.get_session_context_summary(
                uow.session, session_id, max_messages
            )

            if "error" in summary and "Chat session not found" in str(summary.get("error", "")):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )

            return {"code": 200, "data": summary}

    async def get_conversation_summary(self, session_id: str, max_messages: int = 10):
        """Get a summary of the conversation including topics and key information."""
        uow = self.container.make_uow()
        async with uow:
            summary = await self._context_service.get_conversation_summary(
                uow.session, session_id, max_messages
            )

            if "error" in summary and "Chat session not found" in str(summary.get("error", "")):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )

            return {"code": 200, "data": summary}

    async def clear_session_context(self, session_id: str):
        """Clear session context by deleting old messages (keeping last 2 messages)."""
        uow = self.container.make_uow()
        async with uow:
            result = await self._context_service.clear_session_context(uow.session, session_id)

            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )

            return {"code": 200, **result}
