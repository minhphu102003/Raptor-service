import asyncio
from contextlib import asynccontextmanager
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast
from urllib.parse import quote

from .tools.base_tools import create_chat_session as _create_chat_session
from .tools.base_tools import ingest_document as _ingest_document

# Import tool implementations - modify to pass container to tools
# We'll import the functions but modify how they're called
from .tools.base_tools import list_datasets as _list_datasets
from .tools.document_tools import answer_question as _answer_question
from .tools.rag_navigation import rag_path_to_root as _rag_path_to_root
from .tools.rag_node import rag_node_children as _rag_node_children
from .tools.rag_node import rag_node_get as _rag_node_get
from .tools.rag_node import rag_node_navigation as _rag_node_navigation
from .tools.rag_retrieve import rag_retrieve as _rag_retrieve
from .tools.rag_summarize import rag_summarize as _rag_summarize
from .tools.resources import read_resource as _read_resource

# Import for runtime, but avoid type conflicts
try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
    from mcp.server.session import ServerSession
    from mcp.types import Resource, Tool

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not available. Install with: pip install mcp[cli]")

    # Define placeholder class to avoid runtime errors
    class FastMCP:
        def __init__(self, name: str, lifespan=None):
            pass

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def resource(self, uri_template=None):
            def decorator(func):
                return func

            return decorator


logger = logging.getLogger("raptor.mcp.server")


class RaptorMCPService:
    """MCP Service for RAPTOR functionality"""

    def __init__(self, container):
        """Initialize MCP service with required container.

        Args:
            container: The application container with database sessions
        """
        if container is None:
            raise ValueError("Container is required for RaptorMCPService")

        self.container = container
        self.mcp = None
        if MCP_AVAILABLE:
            self.mcp = FastMCP("RAPTOR Service", lifespan=self._lifespan)
            self._register_tools()
            self._register_resources()

    @asynccontextmanager
    async def _lifespan(self, server):  # Remove type annotation to avoid issues
        """Manage MCP server lifecycle"""
        logger.info("Starting RAPTOR MCP server")
        try:
            yield
        finally:
            logger.info("Shutting down RAPTOR MCP server")

    def _register_tools(self):
        """Register all RAPTOR tools with the MCP server"""
        if not self.mcp:
            return

        # Store container reference for use in tool functions
        container = self.container

        # RAG retrieve tool
        @self.mcp.tool()
        async def rag_retrieve_tool(
            dataset_id: str,
            query: str,
            top_k: int = 5,
            levels_cap: Optional[int] = None,
            expand_k: Optional[int] = None,
            reranker: Optional[bool] = None,
            score_threshold: Optional[float] = None,
        ) -> Dict[str, Any]:
            # Pass container to the actual implementation
            return await _rag_retrieve(
                dataset_id,
                query,
                top_k,
                levels_cap,
                expand_k,
                reranker,
                score_threshold,
                container=container,
            )

        # Node metadata tool
        @self.mcp.tool()
        async def rag_node_get_tool(node_id: str) -> Dict[str, Any]:
            return await _rag_node_get(node_id, container=container)

        # Node children tool
        @self.mcp.tool()
        async def rag_node_children_tool(node_id: str) -> Dict[str, Any]:
            return await _rag_node_children(node_id, container=container)

        # Node parent/siblings tool
        @self.mcp.tool()
        async def rag_node_navigation_tool(node_id: str, direction: str) -> Dict[str, Any]:
            return await _rag_node_navigation(node_id, direction, container=container)

        # Path to root tool
        @self.mcp.tool()
        async def rag_path_to_root_tool(node_id: str) -> Dict[str, Any]:
            return await _rag_path_to_root(node_id, container=container)

        # Summarize tool
        @self.mcp.tool()
        async def rag_summarize_tool(node_ids: List[str]) -> Dict[str, Any]:
            return await _rag_summarize(node_ids, container=container)

        # Document ingestion tool (existing)
        @self.mcp.tool()
        async def ingest_document_tool(
            dataset_id: str,
            file_content: str,
            source: Optional[str] = None,
            tags: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            return await _ingest_document(
                dataset_id, file_content, source, tags, container=container
            )

        # Question answering tool (existing)
        @self.mcp.tool()
        async def answer_question_tool(
            dataset_id: str,
            query: str,
            mode: str = "collapsed",
            top_k: int = 5,
            temperature: float = 0.7,
        ) -> Dict[str, Any]:
            return await _answer_question(
                dataset_id, query, mode, top_k, temperature, container=container
            )

        # Dataset management tool (existing)
        @self.mcp.tool()
        async def list_datasets_tool() -> Dict[str, Any]:
            return await _list_datasets(container=container)

        # Chat session tool (existing)
        @self.mcp.tool()
        async def create_chat_session_tool(
            dataset_id: str, title: str = "New Chat Session"
        ) -> Dict[str, Any]:
            return await _create_chat_session(dataset_id, title, container=container)

        logger.info("Registered RAPTOR MCP tools")

    def _register_resources(self):
        """Register all RAPTOR resources with the MCP server"""
        if not self.mcp:
            return

        # Store container reference for use in resource functions
        container = self.container

        # Resource reading handler
        @self.mcp.resource("raptor://{dataset_id}/nodes/{node_id}")
        async def read_resource_tool(dataset_id: str, node_id: str) -> Dict[str, Any]:
            # Construct the URI from the parameters
            uri = f"raptor://{dataset_id}/nodes/{node_id}"
            return await _read_resource(uri, container=container)

    def get_mcp_server(self):
        """Get the MCP server instance"""
        return self.mcp

    async def start_server(self, host: str = "127.0.0.1", port: int = 3333):
        """
        Start the MCP server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        if not self.mcp:
            raise RuntimeError("MCP not available. Install with: pip install mcp[cli]")

        try:
            import uvicorn

            logger.info(f"Starting RAPTOR MCP server on {host}:{port}")
            # This would normally start the server, but we'll let FastAPI handle it
            # when mounted to the main app
        except ImportError:
            logger.error("uvicorn not available for MCP server")
            raise


# For standalone usage, we need to provide a way to create the service
# with a proper container that has database connectivity
def create_standalone_mcp_service(db_dsn: Optional[str] = None, vector_dsn: Optional[str] = None):
    """Create an MCP service for standalone usage with a proper container.

    Args:
        db_dsn: Database connection string for ORM operations
        vector_dsn: Database connection string for vector operations

    Returns:
        RaptorMCPService: Initialized MCP service with proper container
    """
    try:
        # Import required components
        from app.config import settings
        from app.container import Container

        # Use provided DSN or get from environment/settings
        orm_dsn = db_dsn or settings.pg_async_dsn or settings.vector.dsn
        vec_dsn = vector_dsn or settings.vector.dsn

        if not orm_dsn:
            raise ValueError(
                "Database DSN is required. Please provide db_dsn parameter or set PG_ASYNC_DSN environment variable."
            )

        # Create a proper container with database connectivity
        container = Container(orm_async_dsn=orm_dsn, vector_dsn=vec_dsn)

        # Create the MCP service with the proper container
        return RaptorMCPService(container=container)

    except Exception as e:
        logger.error(f"Failed to create standalone MCP service with proper container: {e}")
        raise


# For backward compatibility, we still create a global instance but only when needed
# This global instance is only for backward compatibility and should not be used in the FastAPI app
raptor_mcp_service = None

# Only create the global instance if we're running this module directly
if __name__ == "__main__":
    try:
        raptor_mcp_service = create_standalone_mcp_service()
    except Exception as e:
        logger.warning(f"Could not create global MCP service instance: {e}")
        raptor_mcp_service = None


if __name__ == "__main__":
    # Example of how to run the MCP server standalone
    if MCP_AVAILABLE:
        import asyncio
        import sys

        async def main():
            try:
                # Create service with proper container for standalone usage
                service = create_standalone_mcp_service()
                if len(sys.argv) > 1 and sys.argv[1] == "serve":
                    await service.start_server()
                else:
                    print(
                        "RAPTOR MCP Service ready. Use 'python raptor_mcp_server.py serve' to start server."
                    )
            except Exception as e:
                print(f"Failed to start standalone MCP service: {e}")

        asyncio.run(main())
    else:
        print("MCP not available. Install with: pip install mcp[cli]")
