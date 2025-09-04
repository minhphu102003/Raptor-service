import argparse
from contextlib import asynccontextmanager
import logging
import logging.config
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

from app.config import settings
from app.container import Container
from app.logging_config import setup_logging  # Import the logging setup
from routes.root import root_router

# Import MCP components from local implementation or external package
try:
    # First try to import from external mcp package
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool

    MCP_EXTERNAL = True
    MCP_AVAILABLE = True
except ImportError:
    try:
        # If external package not available, try local implementation
        from mcp.raptor_mcp_server import RaptorMCPService

        MCP_EXTERNAL = False
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False
        MCP_EXTERNAL = False
        print("MCP not available. Install with: pip install mcp[cli]")

# Remove the inline setup_logging function and use the imported one instead

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

    # Check if MCP is explicitly enabled via command line
    mcp_enabled = getattr(app.state, "mcp_enabled", settings.mcp_enabled)

    # Initialize MCP server if available and enabled
    if mcp_enabled and MCP_AVAILABLE and MCP_EXTERNAL:
        try:
            # Import FastMCP here to ensure it's available
            from mcp.server.fastmcp import FastMCP

            # Create MCP server using external package
            mcp = FastMCP("RAPTOR Service")

            # Store MCP server in app state
            app.state.mcp_server = mcp
            print("MCP server initialized (external)")
        except Exception as e:
            print(f"Failed to initialize MCP server: {e}")
    elif mcp_enabled and MCP_AVAILABLE and not MCP_EXTERNAL:
        try:
            # Create MCP server using local implementation
            from mcp.raptor_mcp_server import RaptorMCPService

            # Now we require the container to be passed to RaptorMCPService
            mcp_service = RaptorMCPService(container=app.state.container)
            app.state.mcp_service = mcp_service
            app.state.mcp_server = mcp_service.mcp if hasattr(mcp_service, "mcp") else None
            print("MCP server initialized (local)")
        except Exception as e:
            print(f"Failed to initialize local MCP service: {e}")
    elif not mcp_enabled:
        print("MCP server disabled by configuration")
    else:
        print("MCP not available. Install with: pip install mcp[cli]")

    yield


setup_logging()  # Use the imported setup_logging function


# Parse command line arguments
def create_app():
    parser = argparse.ArgumentParser(description="RAPTOR Service")
    parser.add_argument("--disable-mcp", action="store_true", help="Disable MCP server")
    args, _ = parser.parse_known_args()

    # Create FastAPI app
    app = FastAPI(title="RAPTOR Service", lifespan=lifespan)

    # Store MCP enabled status in app state
    app.state.mcp_enabled = not args.disable_mcp

    return app


app = create_app()

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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router, prefix=settings.api_prefix)

# Add MCP routes if available and enabled
mcp_enabled = getattr(app.state, "mcp_enabled", settings.mcp_enabled)

if mcp_enabled and MCP_AVAILABLE:
    try:
        # Use local SSE endpoint implementation for both external and local MCP
        from mcp.sse_endpoint import mount_sse_endpoints

        mount_sse_endpoints(app)
        print("MCP SSE endpoints mounted")
    except ImportError:
        print("MCP SSE components not available")
elif not mcp_enabled:
    print("MCP routes disabled by configuration")
