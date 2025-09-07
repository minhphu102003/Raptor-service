import argparse
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.container import Container
from app.logging_config import setup_logging  # Import the logging setup
from app.monitor_loop import AddLagHeaderMiddleware, LoopLagMonitor
from routes.root import root_router

# Import MCP components from local implementation or external package
try:
    # First try to import from external mcp package
    from mcp_local.server.fastmcp import FastMCP
    from mcp_local.types import Tool

    MCP_EXTERNAL = True
    MCP_AVAILABLE = True
except ImportError:
    try:
        # If external package not available, try local implementation
        from mcp_local.raptor_mcp_server import RaptorMCPService

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
    app.state.loop_monitor = LoopLagMonitor(interval=0.1)
    asyncio.create_task(app.state.loop_monitor.run())
    # Check if MCP is explicitly enabled via command line or environment
    mcp_enabled = getattr(app.state, "mcp_enabled", settings.mcp.enabled)

    # Initialize MCP server if available and enabled
    if mcp_enabled and MCP_AVAILABLE and MCP_EXTERNAL:
        try:
            # Import FastMCP here to ensure it's available
            from mcp_local.server.fastmcp import FastMCP

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
            from mcp_local.raptor_mcp_server import RaptorMCPService

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


def create_app(mcp_mode: str = "server"):
    """
    Create the FastAPI app.

    Args:
        mcp_mode: MCP mode - "server" for web server, "stdio" for stdio mode
    """
    parser = argparse.ArgumentParser(description="RAPTOR Service")
    parser.add_argument("--disable-mcp", action="store_true", help="Disable MCP server")
    parser.add_argument("--mcp-stdio", action="store_true", help="Run MCP server in stdio mode")
    args, _ = parser.parse_known_args()

    # If stdio mode is requested, run MCP in stdio mode and exit
    if args.mcp_stdio:
        if MCP_AVAILABLE:
            # Run in stdio mode
            async def run_stdio():
                try:
                    from mcp_local.raptor_mcp_server import create_standalone_mcp_service

                    service = create_standalone_mcp_service()
                    print("Starting RAPTOR MCP server in stdio mode...")
                    await service.run_stdio()
                except Exception as e:
                    print(f"Failed to start MCP server in stdio mode: {e}")
                    return 1
                return 0

            # Run the stdio server
            exit_code = asyncio.run(run_stdio())
            exit(exit_code)
        else:
            print("MCP not available. Install with: pip install mcp[cli]")
            exit(1)

    app = FastAPI(title="RAPTOR Service", lifespan=lifespan)

    app.state.mcp_enabled = not args.disable_mcp
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


# We'll move the MCP mounting to the startup event to ensure it runs after the lifespan function
@app.on_event("startup")
async def mount_mcp_endpoints():
    """Mount MCP endpoints after the lifespan function has initialized the MCP service"""
    mcp_enabled = getattr(app.state, "mcp_enabled", settings.mcp.enabled)

    if mcp_enabled and MCP_AVAILABLE:
        try:
            from mcp_local.sse_endpoint import mount_sse_endpoints

            mount_sse_endpoints(app)
            print("MCP SSE endpoints mounted")

            # Mount the MCP protocol endpoints to the FastAPI app
            # This is needed for the core MCP functionality
            if hasattr(app.state, "mcp_service") and app.state.mcp_service:
                try:
                    app.state.mcp_service.mount_to_fastapi(app, path="/mcp")
                    print("MCP protocol endpoints mounted")
                except Exception as e:
                    print(f"Failed to mount MCP protocol endpoints: {e}")
            elif hasattr(app.state, "mcp_server") and app.state.mcp_server:
                # For external MCP implementation, we need to check if it has streamable_http_app method
                try:
                    if hasattr(app.state.mcp_server, "streamable_http_app"):
                        app.mount("/mcp", app.state.mcp_server.streamable_http_app())
                        print("MCP protocol endpoints mounted (external)")
                    else:
                        print("External MCP server does not support streamable HTTP app mounting")
                except Exception as e:
                    print(f"Failed to mount external MCP protocol endpoints: {e}")
            else:
                print("MCP service/server not available for mounting")
        except ImportError:
            print("MCP components not available")
        except Exception as e:
            print(f"Failed to mount MCP endpoints: {e}")
    elif not mcp_enabled:
        print("MCP routes disabled by configuration")
