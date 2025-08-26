from fastapi import APIRouter, Depends

from .document_routes import router as documents_router


def auth_dep(): ...


root_router = APIRouter()

api_v1 = APIRouter(prefix="/v1", dependencies=[Depends(auth_dep)])

api_v1.include_router(documents_router, prefix="/documents", tags=["documents"])

root_router.include_router(api_v1)
