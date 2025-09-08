import argparse
import asyncio
from contextlib import asynccontextmanager
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set the event loop policy for Windows compatibility with psycopg
if sys.platform == "win32":
    from asyncio import WindowsSelectorEventLoopPolicy

    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

from app.config import settings
from app.container import Container
from app.logging_config import setup_logging  # Import the logging setup
from app.monitor_loop import AddLagHeaderMiddleware, LoopLagMonitor
from routes.root import root_router

# Fix the DSN to ensure it uses the correct driver
ASYNC_DSN = settings.pg_async_dsn or settings.vector.dsn

# Ensure the DSN uses the correct driver
if ASYNC_DSN and not ASYNC_DSN.startswith("postgresql+psycopg://"):
    if ASYNC_DSN.startswith("postgresql://"):
        ASYNC_DSN = ASYNC_DSN.replace("postgresql://", "postgresql+psycopg://")
    elif ASYNC_DSN.startswith("postgresql+asyncpg://"):
        ASYNC_DSN = ASYNC_DSN.replace("postgresql+asyncpg://", "postgresql+psycopg://")

VECTOR_DSN = settings.vector.dsn

# Ensure the DSN uses the correct driver
if VECTOR_DSN and not VECTOR_DSN.startswith("postgresql+psycopg://"):
    if VECTOR_DSN.startswith("postgresql://"):
        VECTOR_DSN = VECTOR_DSN.replace("postgresql://", "postgresql+psycopg://")
    elif VECTOR_DSN.startswith("postgresql+asyncpg://"):
        VECTOR_DSN = VECTOR_DSN.replace("postgresql+asyncpg://", "postgresql+psycopg://")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container(orm_async_dsn=ASYNC_DSN, vector_dsn=VECTOR_DSN)
    app.state.loop_monitor = LoopLagMonitor(interval=0.1)
    asyncio.create_task(app.state.loop_monitor.run())

    yield


setup_logging()  # Use the imported setup_logging function


def create_app():
    """
    Create the FastAPI app.
    """
    app = FastAPI(title="RAPTOR Service", lifespan=lifespan)

    return app


app = create_app()


# Add the AddLagHeaderMiddleware in the startup event when the monitor is available
@app.on_event("startup")
async def setup_middleware():
    # Add the middleware with the actual monitor instance
    app.add_middleware(AddLagHeaderMiddleware, monitor=app.state.loop_monitor)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://172.18.0.1:45094",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Event-Loop-Lag-p95-ms"],
)

app.include_router(root_router, prefix=settings.api_prefix)
