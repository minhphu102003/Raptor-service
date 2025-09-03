import time
from typing import Annotated, Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select

from controllers.dataset_controller import DatasetController
from db.models.chat import ChatMessageORM, ChatSessionORM, MessageRole
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
    assistant_id: Optional[str] = None
    assistant_config: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    query: str
    dataset_id: str
    session_id: Optional[str] = None

    # Retrieval parameters
    top_k: int = 5
    expand_k: int = 5
    mode: Literal["tree", "chunk"] = "tree"

    # Answer generation parameters
    answer_model: Literal["DeepSeek-V3", "GPT-4o-mini", "Gemini-2.5-Flash", "Claude-3.5-Haiku"] = (
        "DeepSeek-V3"
    )
    temperature: float = 0.7
    max_tokens: int = 4000
    stream: bool = False


class EnhancedChatMessageRequest(ChatMessageRequest):
    """Enhanced chat message request with additional context options"""

    use_enhanced_context: bool = True
    max_context_messages: int = 6
    additional_context: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    assistant_config: Optional[dict] = None


@router.post("/sessions", summary="Create new chat session")
async def create_chat_session(request: Request, body: CreateSessionRequest):
    """
    Create a new chat session for a specific dataset/knowledge base.
    """
    container = request.app.state.container
    uow = container.make_uow()

    try:
        async with uow:
            result = await _CHAT.create_session(
                db_session=uow.session,
                dataset_id=body.dataset_id,
                title=body.title,
                user_id=body.user_id,
                assistant_id=body.assistant_id,
                assistant_config=body.assistant_config,
            )
            return {"code": 200, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}",
        )


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
    container = request.app.state.container
    uow = container.make_uow()

    try:
        async with uow:
            sessions = await _CHAT.list_sessions(
                db_session=uow.session,
                user_id=user_id,
                dataset_id=dataset_id,
                assistant_id=assistant_id,
                limit=limit,
                offset=offset,
            )
            return {"code": 200, "data": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chat sessions: {str(e)}",
        )


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


@router.get("/sessions/{session_id}/context", summary="Get session context")
async def get_session_context(session_id: str, request: Request):
    """
    Get session context including chat history and associated information.

    Args:
        session_id: The chat session ID

    Returns:
        Session context information
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        # Get session context from answer service
        context = await _ANSWER.get_session_context(uow.session, session_id)

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        return {"code": 200, "data": context}


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
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        # Get session context from answer service
        context = await _ANSWER.get_session_context(uow.session, session_id, max_messages)

        if "error" in context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        # Create a summary of the context
        summary = {
            "session_id": context["session_id"],
            "dataset_id": context["dataset_id"],
            "assistant_id": context["assistant_id"],
            "message_count": context["message_count"],
            "recent_message_count": len(context["recent_messages"]),
            "system_prompt": context["system_prompt"],
            "model_info": context["assistant_config"].get("model")
            if context["assistant_config"]
            else None,
            "last_message_timestamp": context["recent_messages"][-1]["timestamp"]
            if context["recent_messages"]
            else None,
        }

        return {"code": 200, "data": summary}


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
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        # Get conversation summary from answer service
        summary = await _ANSWER.summarize_conversation_context(
            uow.session, session_id, max_messages
        )

        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        return {"code": 200, "data": summary}


@router.post("/sessions/{session_id}/context/clear", summary="Clear session context")
async def clear_session_context(session_id: str, request: Request):
    """
    Clear session context by deleting old messages (keeping last 2 messages).

    Args:
        session_id: The chat session ID

    Returns:
        Confirmation of context clearing
    """
    container = request.app.state.container
    uow = container.make_uow()

    async with uow:
        # First verify session exists
        session_data = await _CHAT.get_session(uow.session, session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
            )

        # Get all messages for this session
        messages = await _CHAT.get_messages(uow.session, session_id, limit=1000)

        # If more than 2 messages, delete older ones (keep last 2)
        if len(messages) > 2:
            # Get message IDs to delete (all except last 2)
            messages_to_delete = messages[:-2]

            # Delete older messages
            for msg in messages_to_delete:
                stmt = delete(ChatMessageORM).where(ChatMessageORM.message_id == msg["message_id"])
                await uow.session.execute(stmt)

            # Update session message count
            session_result = await uow.session.execute(
                select(ChatSessionORM).where(ChatSessionORM.session_id == session_id)
            )
            chat_session = session_result.scalar_one_or_none()
            if chat_session:
                chat_session.message_count = 2
                await uow.session.commit()

            return {
                "code": 200,
                "message": f"Deleted {len(messages_to_delete)} old messages. Kept last 2 messages.",
            }
        else:
            return {
                "code": 200,
                "message": "Not enough messages to clear context. Session has 2 or fewer messages.",
            }


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

        # Create a RetrieveBody object from ChatMessageRequest
        from services.retrieval.retrieval_service import RetrieveBody

        retrieve_body = RetrieveBody(
            dataset_id=body.dataset_id,
            query=body.query,
            mode="collapsed" if body.mode == "tree" else "traversal",
            top_k=body.top_k,
            expand_k=body.expand_k,
            levels_cap=0,  # Default value
            use_reranker=False,  # Default value
            reranker_model=None,  # Default value
            byok_voyage_api_key=None,  # Default value
        )

        # Get response with context using the retrieve_body and additional parameters
        result = await _ANSWER.answer_with_context(
            retrieve_body,
            repo=repo,
            db_session=uow.session,
            session_id=body.session_id,
            answer_model=body.answer_model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            stream=body.stream,
        )

        return result


@router.post("/chat/enhanced", summary="Send chat message with enhanced context")
async def send_enhanced_chat_message(body: EnhancedChatMessageRequest, request: Request):
    """
    Send a message and get AI response with enhanced context awareness.

    Args:
        body: Enhanced chat message and parameters

    Returns:
        AI response with enhanced context
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

        # Create a RetrieveBody object from EnhancedChatMessageRequest
        from services.retrieval.retrieval_service import RetrieveBody

        retrieve_body = RetrieveBody(
            dataset_id=body.dataset_id,
            query=body.query,
            mode="collapsed" if body.mode == "tree" else "traversal",
            top_k=body.top_k,
            expand_k=body.expand_k,
            levels_cap=0,  # Default value
            use_reranker=False,  # Default value
            reranker_model=None,  # Default value
            byok_voyage_api_key=None,  # Default value
        )

        # Retrieve relevant passages using the full capabilities of RetrievalService
        ret = await _SERVICE.retrieve(retrieve_body, repo=repo)
        if ret.get("code") != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve context",
            )

        passages = ret.get("data", [])
        # Use 'content' if available, otherwise fallback to 'text'
        passages_ctx = "\n\n".join(
            [p.get("content", p.get("text", "")) for p in passages[: body.top_k]]
        )

        # Build enhanced context prompt with full session context
        if body.session_id:
            prompt = await _ANSWER.build_enhanced_context_prompt(
                uow.session, body.session_id, body.query, passages_ctx, body.additional_context
            )
        else:
            # Use a simpler prompt when no session context is available
            prompt = await _ANSWER.build_prompt(body.query, passages[: body.top_k])

        # Generate response with enhanced prompt
        client = _model_registry.get_client(body.answer_model, body)

        start_time = time.time()

        if body.stream:

            async def _gen():
                response_chunks = []
                async for chunk in client.astream(
                    prompt=prompt, temperature=body.temperature, max_tokens=body.max_tokens
                ):
                    response_chunks.append(chunk)
                    yield chunk

                # Calculate processing time
                processing_time = int((time.time() - start_time) * 1000)

                # Save messages if session exists
                if body.session_id:
                    full_response = "".join(response_chunks)
                    await _ANSWER.save_message(
                        uow.session,
                        body.session_id,
                        MessageRole.assistant,
                        full_response,
                        context_passages=passages[: body.top_k],
                        retrieval_query=body.query,
                        model_used=body.answer_model,
                        generation_params={
                            "temperature": body.temperature,
                            "max_tokens": body.max_tokens,
                            "model": body.answer_model,
                        },
                        processing_time_ms=processing_time,
                    )

            return StreamingResponse(_gen(), media_type="text/plain")

        # Non-streaming response
        text = await client.generate(
            prompt=prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        # Save messages if session exists
        if body.session_id:
            await _ANSWER.save_message(
                uow.session,
                body.session_id,
                MessageRole.assistant,
                text,
                context_passages=passages[: body.top_k],
                retrieval_query=body.query,
                model_used=body.answer_model,
                generation_params={
                    "temperature": body.temperature,
                    "max_tokens": body.max_tokens,
                    "model": body.answer_model,
                },
                processing_time_ms=processing_time,
            )

        return {
            "answer": text,
            "model": body.answer_model,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": passages[: body.top_k],
            "session_id": body.session_id,
            "processing_time_ms": processing_time,
        }
