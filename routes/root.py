from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .assistant_routes import router as assistant_router
from .chat_context_routes import router as chat_context_router
from .chat_message_routes import router as chat_message_router
from .chat_session_routes import router as chat_session_router
from .dataset_routes import router as datasets_router
from .document_routes import router as documents_router


root_router = APIRouter()


# Health check endpoint - placed at the root level
@root_router.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "raptor-service", "version": "1.0.0"},
    )


# Remove the separate api_v1 router since root_router will be prefixed with /v1 in main.py
root_router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
root_router.include_router(documents_router, prefix="/documents", tags=["documents"])
root_router.include_router(assistant_router, prefix="/ai", tags=["assistants"])
# Remove the old chat router and add the new ones
# root_router.include_router(chat_router, prefix="/datasets/chat", tags=["chat"])
root_router.include_router(chat_session_router, prefix="/datasets/chat", tags=["chat"])
root_router.include_router(chat_message_router, prefix="/datasets/chat", tags=["chat"])
root_router.include_router(chat_context_router, prefix="/datasets/chat", tags=["chat"])