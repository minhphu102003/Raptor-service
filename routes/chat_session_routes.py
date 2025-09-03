import time
from typing import Annotated, Optional

from fastapi import APIRouter, Query, Request

from controllers.chat_controller import ChatController
from dtos.chat_dto import CreateSessionRequest, UpdateSessionRequest
from services import ChatService

router = APIRouter()


@router.post("/sessions", summary="Create new chat session")
async def create_chat_session(request: Request, body: CreateSessionRequest):
    """
    Create a new chat session for a specific dataset/knowledge base.
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.create_session(body)


@router.get("/sessions", summary="List chat sessions")
async def list_chat_sessions(
    request: Request,
    user_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List chat sessions with optional filtering by user_id, dataset_id, or assistant_id.
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.list_sessions(user_id, dataset_id, assistant_id, limit, offset)


@router.get("/sessions/{session_id}", summary="Get chat session")
async def get_chat_session(session_id: str, request: Request):
    """
    Get details of a specific chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Session details
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.get_session(session_id)


@router.put("/sessions/{session_id}", summary="Update chat session")
async def update_chat_session(session_id: str, request: Request, body: UpdateSessionRequest):
    """
    Update a chat session (title, assistant config, etc.).

    Args:
        session_id: The chat session ID
        body: Update parameters

    Returns:
        Updated session information
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.update_session(session_id, body)


@router.delete("/sessions/{session_id}", summary="Delete chat session")
async def delete_chat_session(session_id: str, request: Request):
    """
    Delete (archive) a chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Deletion confirmation
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.delete_session(session_id)


@router.get("/sessions/{session_id}/messages", summary="Get chat messages")
async def get_chat_messages(
    session_id: str,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    Get messages from a chat session.

    Args:
        session_id: The chat session ID
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        List of chat messages
    """
    chat_service = ChatService()
    controller = ChatController(request, chat_service)
    return await controller.get_messages(session_id, limit, offset)
