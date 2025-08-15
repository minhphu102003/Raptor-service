from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.container import Container
from interfaces_adaptor.http.controllers import router as ingest_router

ASYNC_DSN = settings.pg_async_dsn or settings.vector.dsn.replace(
    "postgresql://", "postgresql+asyncpg://"
)
VECTOR_DSN = settings.vector.dsn


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container(orm_async_dsn=ASYNC_DSN, vector_dsn=VECTOR_DSN)
    yield


app = FastAPI(title="RAPTOR Service", lifespan=lifespan)
app.include_router(ingest_router, prefix=settings.api_prefix)
