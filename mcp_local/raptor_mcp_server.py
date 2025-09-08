import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context, FastMCP

# Import tool implementations
from .tools.base_tools import create_chat_session as _create_chat_session
from .tools.base_tools import ingest_document as _ingest_document
from .tools.base_tools import list_datasets as _list_datasets
from .tools.document_tools import answer_question as _answer_question
from .tools.rag_navigation import rag_path_to_root as _rag_path_to_root
from .tools.rag_node import rag_node_children as _rag_node_children
from .tools.rag_node import rag_node_get as _rag_node_get
from .tools.rag_node import rag_node_navigation as _rag_node_navigation
from .tools.rag_retrieve import rag_retrieve as _rag_retrieve
from .tools.rag_summarize import rag_summarize as _rag_summarize
from .tools.resources import read_resource as _read_resource

logger = logging.getLogger("raptor.mcp.server")

# Create the MCP instance
mcp = FastMCP("RAPTOR Service")


class RaptorMCPService:
    """MCP Service for RAPTOR functionality"""

    def __init__(self, container):
        """Initialize MCP service with required container."""
        self.container = container
        self.mcp = mcp
        self._register_tools()

    def _register_tools(self):
        """Register all RAPTOR tools with the MCP server"""
        container = self.container

        # RAG retrieve tool
        @self.mcp.tool(
            name="rag_retrieve",
            description="Retrieve relevant nodes from a RAPTOR tree based on a query",
            tags={"rag", "retrieve", "search"},
        )
        async def rag_retrieve_tool(
            dataset_id: str,
            query: str,
            top_k: int = 5,
            levels_cap: Optional[int] = None,
            expand_k: Optional[int] = None,
            reranker: Optional[bool] = None,
            score_threshold: Optional[float] = None,
        ) -> Dict[str, Any]:
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

        # # Node metadata tool
        # @self.mcp.tool(
        #     name="rag_node_get",
        #     description="Get metadata for a specific RAPTOR node",
        #     tags={"rag", "node", "metadata"}
        # )
        # async def rag_node_get_tool(node_id: str) -> Dict[str, Any]:
        #     return await _rag_node_get(node_id, container=container)

        # # Node children tool
        # @self.mcp.tool(
        #     name="rag_node_children",
        #     description="Get children of a specific RAPTOR node",
        #     tags={"rag", "node", "children"}
        # )
        # async def rag_node_children_tool(node_id: str) -> Dict[str, Any]:
        #     return await _rag_node_children(node_id, container=container)

        # # Node parent/siblings tool
        # @self.mcp.tool(
        #     name="rag_node_navigation",
        #     description="Navigate RAPTOR tree structure (parent, siblings)",
        #     tags={"rag", "node", "navigation"}
        # )
        # async def rag_node_navigation_tool(node_id: str, direction: str) -> Dict[str, Any]:
        #     return await _rag_node_navigation(node_id, direction, container=container)

        # # Path to root tool
        # @self.mcp.tool(
        #     name="rag_path_to_root",
        #     description="Get path from a node to the root of the RAPTOR tree",
        #     tags={"rag", "node", "path"}
        # )
        # async def rag_path_to_root_tool(node_id: str) -> Dict[str, Any]:
        #     return await _rag_path_to_root(node_id, container=container)

        # # Summarize tool
        # @self.mcp.tool(
        #     name="rag_summarize",
        #     description="Generate summary for a set of RAPTOR nodes",
        #     tags={"rag", "summarize"}
        # )
        # async def rag_summarize_tool(node_ids: List[str]) -> Dict[str, Any]:
        #     return await _rag_summarize(node_ids, container=container)

        # # Document ingestion tool
        # @self.mcp.tool(
        #     name="ingest_document",
        #     description="Ingest a document into a RAPTOR dataset",
        #     tags={"document", "ingest"}
        # )
        # async def ingest_document_tool(
        #     dataset_id: str,
        #     file_content: str,
        #     source: Optional[str] = None,
        #     tags: Optional[List[str]] = None,
        # ) -> Dict[str, Any]:
        #     return await _ingest_document(
        #         dataset_id, file_content, source, tags, container=container
        #     )

        # # Question answering tool
        # @self.mcp.tool(
        #     name="answer_question",
        #     description="Answer a question using RAPTOR tree retrieval",
        #     tags={"rag", "question", "answer"}
        # )
        # async def answer_question_tool(
        #     dataset_id: str,
        #     query: str,
        #     mode: str = "collapsed",
        #     top_k: int = 5,
        #     temperature: float = 0.7,
        # ) -> Dict[str, Any]:
        #     return await _answer_question(
        #         dataset_id, query, mode, top_k, temperature, container=container
        #     )

        # # Dataset management tool
        # @self.mcp.tool(
        #     name="list_datasets",
        #     description="List all available RAPTOR datasets",
        #     tags={"dataset", "list"}
        # )
        # async def list_datasets_tool() -> Dict[str, Any]:
        #     return await _list_datasets(container=container)

        # # Chat session tool
        # @self.mcp.tool(
        #     name="create_chat_session",
        #     description="Create a new chat session for a dataset",
        #     tags={"chat", "session"}
        # )
        # async def create_chat_session_tool(
        #     dataset_id: str, title: str = "New Chat Session"
        # ) -> Dict[str, Any]:
        #     return await _create_chat_session(dataset_id, title, container=container)

        # logger.info("Registered RAPTOR MCP tools")

    def get_mcp_server(self):
        """Get the MCP server instance"""
        return self.mcp

    def mount_to_fastapi(self, app, path: str = "/mcp"):
        """Mount the MCP server to a FastAPI application"""
        app.mount(path, self.mcp.http_app())
        logger.info(f"MCP server mounted to {path}")

    async def start_server(self, host: str = "127.0.0.1", port: int = 3333):
        """Start the MCP server"""
        from fastapi import FastAPI
        import uvicorn

        app = FastAPI()
        app.mount("/mcp", self.mcp.http_app())
        logger.info("MCP server mounted to /mcp")

        logger.info(f"Starting RAPTOR MCP server on {host}:{port}")
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def run_stdio(self):
        """Run the MCP server over stdio"""
        await self.mcp.run(transport="stdio")


def initialize_mcp_with_container(container):
    """Initialize MCP tools with container for database connectivity"""
    service = RaptorMCPService(container)
    return service.mcp


def create_standalone_mcp_service(db_dsn: Optional[str] = None, vector_dsn: Optional[str] = None):
    """Create an MCP service for standalone usage with a proper container."""
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

        # Initialize MCP with the container
        mcp_instance = initialize_mcp_with_container(container)

        return mcp_instance

    except Exception as e:
        logger.error(f"Failed to create standalone MCP service with proper container: {e}")
        raise


if __name__ == "__main__":
    import argparse
    import sys

    # Set the event loop policy for Windows compatibility with psycopg
    if sys.platform == "win32":
        from asyncio import WindowsSelectorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3333)
    parser.add_argument("--path", default="/mcp")
    args = parser.parse_args()

    # Create service with proper container for standalone usage
    mcp_instance = create_standalone_mcp_service()

    if args.mode == "stdio":
        print("Starting RAPTOR MCP server in stdio mode...")
        mcp_instance.run(transport="stdio")
    else:
        print(f"Starting RAPTOR MCP server on {args.host}:{args.port}...")
        mcp_instance.run(transport="http", host=args.host, port=args.port, path=args.path)
