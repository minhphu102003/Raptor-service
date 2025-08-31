from fastapi import APIRouter, Depends

from .chat_routes import router as chat_router
from .dataset_routes import router as datasets_router
from .document_routes import router as documents_router


def auth_dep(): ...


root_router = APIRouter()

api_v1 = APIRouter(prefix="/v1", dependencies=[Depends(auth_dep)])

api_v1.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
api_v1.include_router(documents_router, prefix="/documents", tags=["documents"])
api_v1.include_router(chat_router, prefix="/datasets/chat", tags=["chat"])

root_router.include_router(api_v1)
