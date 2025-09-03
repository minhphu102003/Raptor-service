from functools import wraps
import logging
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status

from dtos.chat_dto import CreateSessionRequest
from services import ChatService
from services.shared.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


def handle_service_errors(func: Callable) -> Callable:
    """Decorator to handle common service errors"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
            )

    return wrapper


class ChatController:
    """Controller for chat HTTP endpoints"""

    def __init__(self, request: Request, chat_service: ChatService):
        self.request = request
        self.container = request.app.state.container
        self.service = chat_service

    @handle_service_errors
    async def create_session(self, body: CreateSessionRequest):
        """Create a new chat session"""
        uow = self.container.make_uow()
        async with uow:
            result = await self.service.create_session(
                db_session=uow.session,
                dataset_id=body.dataset_id,
                title=body.title,
                user_id=body.user_id,
                assistant_id=body.assistant_id,
                assistant_config=body.assistant_config,
            )
            return {"code": 200, "data": result}

    @handle_service_errors
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ):
        """List chat sessions with optional filtering"""
        uow = self.container.make_uow()
        async with uow:
            sessions = await self.service.list_sessions(
                db_session=uow.session,
                user_id=user_id,
                dataset_id=dataset_id,
                assistant_id=assistant_id,
                limit=limit,
                offset=offset,
            )
            return {"code": 200, "data": sessions}

    @handle_service_errors
    async def get_session(self, session_id: str):
        """Get details of a specific chat session"""
        uow = self.container.make_uow()
        async with uow:
            session_data = await self.service.get_session(uow.session, session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )
            return {"code": 200, "data": session_data}

    @handle_service_errors
    async def update_session(self, session_id: str, body: CreateSessionRequest):
        """Update a chat session"""
        uow = self.container.make_uow()
        async with uow:
            session_data = await self.service.update_session(
                uow.session, session_id, title=body.title, assistant_config=body.assistant_config
            )
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )
            return {"code": 200, "data": session_data}

    @handle_service_errors
    async def delete_session(self, session_id: str):
        """Delete (archive) a chat session"""
        uow = self.container.make_uow()
        async with uow:
            success = await self.service.delete_session(uow.session, session_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )
            return {"code": 200, "message": "Session deleted successfully"}

    @handle_service_errors
    async def get_messages(self, session_id: str, limit: int = 50, offset: int = 0):
        """Get messages from a chat session"""
        uow = self.container.make_uow()
        async with uow:
            messages = await self.service.get_messages(
                uow.session, session_id, limit=limit, offset=offset
            )
            return {"code": 200, "data": messages}
