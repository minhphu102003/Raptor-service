from fastapi import APIRouter, Request

from controllers.chat_context_controller import ChatContextController
from services import AnswerService

router = APIRouter()


@router.get("/sessions/{session_id}/context", summary="Get session context")
async def get_session_context(session_id: str, request: Request):
    """
    Get session context including chat history and associated information.

    Args:
        session_id: The chat session ID

    Returns:
        Session context information
    """
    # Get the answer service from the app state
    answer_service = request.app.state.answer_service
    controller = ChatContextController(request, answer_service)
    return await controller.get_session_context(session_id)


@router.get("/sessions/{session_id}/context/summary", summary="Get session context summary")
async def get_session_context_summary(session_id: str, request: Request, max_messages: int = 10):
    """
    Get a summary of session context including recent messages and metadata.

    Args:
        session_id: The chat session ID
        max_messages: Maximum number of recent messages to include in summary

    Returns:
        Session context summary
    """
    # Get the answer service from the app state
    answer_service = request.app.state.answer_service
    controller = ChatContextController(request, answer_service)
    return await controller.get_session_context_summary(session_id, max_messages)


@router.get(
    "/sessions/{session_id}/context/conversation-summary", summary="Get conversation summary"
)
async def get_conversation_summary(session_id: str, request: Request, max_messages: int = 10):
    """
    Get a summary of the conversation including topics and key information.

    Args:
        session_id: The chat session ID
        max_messages: Maximum number of recent messages to analyze

    Returns:
        Conversation summary
    """
    # Get the answer service from the app state
    answer_service = request.app.state.answer_service
    controller = ChatContextController(request, answer_service)
    return await controller.get_conversation_summary(session_id, max_messages)


@router.post("/sessions/{session_id}/context/clear", summary="Clear session context")
async def clear_session_context(session_id: str, request: Request):
    """
    Clear session context by deleting old messages (keeping last 2 messages).

    Args:
        session_id: The chat session ID

    Returns:
        Confirmation of context clearing
    """
    # Get the answer service from the app state
    answer_service = request.app.state.answer_service
    controller = ChatContextController(request, answer_service)
    return await controller.clear_session_context(session_id)
