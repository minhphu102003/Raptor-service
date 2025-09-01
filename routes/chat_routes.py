from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from controllers.dataset_controller import DatasetController
from repositories.retrieval_repo import RetrievalRepo
from services.core.chat_service import ChatService
from services.embedding.embedding_query_service import EmbeddingService
from services.providers.fpt_llm.client import FPTLLMClient
from services.providers.gemini_chat.llm import GeminiChatLLM
from services.providers.model_registry import ModelRegistry
from services.providers.openai_chat.openai_client_async import OpenAIClientAsync
from services.providers.voyage.voyage_client import VoyageEmbeddingClientAsync
from services.retrieval.answer_service import AnswerService
from services.retrieval.query_rewrite_service import QueryRewriteService
from services.retrieval.retrieval_service import RetrievalService

router = APIRouter()

# Initialize services (same as document_routes.py)
_FPT = FPTLLMClient(model="DeepSeek-V3")
_VOY = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)
_REWRITE = QueryRewriteService(fpt_client=_FPT)
_EMBED = EmbeddingService(voyage_client_async=_VOY)
_SERVICE = RetrievalService(rewrite_svc=_REWRITE, embed_svc=_EMBED)
_GEMINI = GeminiChatLLM(model="gemini-2.5-flash")
_OPENAI = OpenAIClientAsync(model="gpt-4o-mini")

_model_registry = ModelRegistry(
    fpt_client=_FPT,
    openai_client=_OPENAI,
    gemini_client=_GEMINI,
    anthropic_client=None,
)

_ANSWER = AnswerService(retrieval_svc=_SERVICE, model_registry=_model_registry)
_CHAT = ChatService()


# Request/Response Models
class CreateSessionRequest(BaseModel):
    dataset_id: str
    title: str = "New Chat"
    user_id: Optional[str] = None
    assistant_config: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    query: str
    dataset_id: str
    session_id: Optional[str] = None

    # Retrieval parameters
    top_k: int = 5
    mode: Literal["tree", "chunk"] = "tree"

    # Answer generation parameters
    answer_model: Literal["DeepSeek-V3", "GPT-4o-mini", "Gemini-2.5-Flash", "Claude-3.5-Haiku"] = (
        "DeepSeek-V3"
    )
    temperature: float = 0.7
    max_tokens: int = 4000
    stream: bool = False


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    assistant_config: Optional[dict] = None


@router.post("/sessions", summary="Create new chat session")
async def create_chat_session(request: Request, body: CreateSessionRequest):
    """
    Create a new chat session for a specific dataset/knowledge base.

    Args:
        body: Session creation parameters

    Returns:
        Created session information
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        # Validate dataset exists
        dataset_controller = DatasetController(request)
        try:
            await dataset_controller.validate_dataset(body.dataset_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset ID: {body.dataset_id}",
            )

        # Create session
        session_data = await _CHAT.create_session(
            uow.session,
            dataset_id=body.dataset_id,
            title=body.title,
            user_id=body.user_id,
            assistant_config=body.assistant_config,
        )

        return {"code": 200, "data": session_data}


@router.get("/sessions", summary="List chat sessions")
async def list_chat_sessions(
    request: Request,
    user_id: Annotated[Optional[str], Query()] = None,
    dataset_id: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List chat sessions with optional filtering.

    Args:
        user_id: Filter by user ID
        dataset_id: Filter by dataset ID
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of chat sessions
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        sessions = await _CHAT.list_sessions(
            uow.session, user_id=user_id, dataset_id=dataset_id, limit=limit, offset=offset
        )

        return {"code": 200, "data": sessions}


@router.get("/sessions/{session_id}", summary="Get chat session")
async def get_chat_session(session_id: str, request: Request):
    """
    Get details of a specific chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Session details
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        session_data = await _CHAT.get_session(uow.session, session_id)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        return {"code": 200, "data": session_data}


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
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        session_data = await _CHAT.update_session(
            uow.session, session_id, title=body.title, assistant_config=body.assistant_config
        )

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        return {"code": 200, "data": session_data}


@router.delete("/sessions/{session_id}", summary="Delete chat session")
async def delete_chat_session(session_id: str, request: Request):
    """
    Delete (archive) a chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Deletion confirmation
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        success = await _CHAT.delete_session(uow.session, session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        return {"code": 200, "message": "Session deleted successfully"}


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
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        messages = await _CHAT.get_messages(uow.session, session_id, limit=limit, offset=offset)

        return {"code": 200, "data": messages}


@router.post("/chat", summary="Send chat message")
async def send_chat_message(body: ChatMessageRequest, request: Request):
    """
    Send a message and get AI response with chat context.

    Args:
        body: Chat message and parameters

    Returns:
        AI response with context
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        repo = RetrievalRepo(uow)

        # Validate dataset
        dataset_controller = DatasetController(request)
        try:
            await dataset_controller.validate_dataset(body.dataset_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset ID: {body.dataset_id}",
            )

        # If session_id provided, validate it exists
        if body.session_id:
            session_data = await _CHAT.get_session(uow.session, body.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                )

        # Get response with context
        result = await _ANSWER.answer_with_context(
            body, repo=repo, db_session=uow.session, session_id=body.session_id
        )

        return result
