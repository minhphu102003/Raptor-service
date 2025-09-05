import logging
import time

from fastapi import APIRouter, Request

from controllers.chat_message_controller import ChatMessageController
from dtos.chat_dto import ChatMessageRequest, EnhancedChatMessageRequest
from services import (
    AnswerService,
    ChatService,
    EmbeddingQueryService,
    FPTLLMClient,
    GeminiChatLLM,
    ModelRegistry,
    OpenAIClientAsync,
    RetrievalService,
    VoyageEmbeddingClientAsync,
)

logger = logging.getLogger("raptor.retrieve.routes")

router = APIRouter()


@router.post("/chat", summary="Send chat message")
async def send_chat_message(body: ChatMessageRequest, request: Request):
    """
    Send a message and get AI response with chat context.

    Args:
        body: Chat message and parameters

    Returns:
        AI response with context
    """
    logger.info(f"Received chat message request: {body.query}")
    start_time = time.time()

    # Initialize services
    logger.debug("Initializing services")
    _fpt = FPTLLMClient(model="DeepSeek-V3")
    _voy = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)
    _embed = EmbeddingQueryService(voyage_client_async=_voy)
    _service = RetrievalService(embed_svc=_embed)
    _gemini = GeminiChatLLM(model="gemini-2.5-flash")
    _openai = OpenAIClientAsync(model="gpt-4o-mini")

    _model_registry = ModelRegistry(
        fpt_client=_fpt,
        openai_client=_openai,
        gemini_client=_gemini,
        anthropic_client=None,
    )

    answer_service = AnswerService(retrieval_svc=_service, model_registry=_model_registry)
    chat_service = ChatService()

    controller = ChatMessageController(request, chat_service, answer_service)
    result = await controller.send_chat_message(body)

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(f"Chat message request completed in {processing_time}ms")

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
    logger.info(f"Received enhanced chat message request: {body.query}")
    start_time = time.time()

    # Initialize services
    logger.debug("Initializing services")
    _fpt = FPTLLMClient(model="DeepSeek-V3")
    _voy = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)
    _embed = EmbeddingQueryService(voyage_client_async=_voy)
    _service = RetrievalService(embed_svc=_embed)
    _gemini = GeminiChatLLM(model="gemini-2.5-flash")
    _openai = OpenAIClientAsync(model="gpt-4o-mini")

    _model_registry = ModelRegistry(
        fpt_client=_fpt,
        openai_client=_openai,
        gemini_client=_gemini,
        anthropic_client=None,
    )

    answer_service = AnswerService(retrieval_svc=_service, model_registry=_model_registry)
    chat_service = ChatService()

    controller = ChatMessageController(request, chat_service, answer_service)
    result = await controller.send_enhanced_chat_message(body)

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(f"Enhanced chat message request completed in {processing_time}ms")

    return result
