import asyncio
from contextlib import asynccontextmanager
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

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


class RaptorMCPService:
    """MCP Service for RAPTOR functionality using standard MCP library"""

    def __init__(self, container):
        """Initialize MCP service with required container."""
        self.container = container
        self.mcp_server = self._create_mcp_server()

    def _create_mcp_server(self) -> Server:
        """Create a standard MCP server with all RAPTOR tools"""
        server = Server("RAPTOR Service")

        # Register tools with the server
        @server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="rag_retrieve",
                    description="Retrieve relevant nodes from a RAPTOR tree based on a query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dataset_id": {"type": "string"},
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 5},
                            "levels_cap": {"type": "integer"},
                            "expand_k": {"type": "integer"},
                            "reranker": {"type": "boolean"},
                            "score_threshold": {"type": "number"},
                        },
                        "required": ["dataset_id", "query"],
                    },
                ),
                types.Tool(
                    name="list_datasets",
                    description="List all available RAPTOR datasets with detailed information including document counts, processing status, and statistics",
                    inputSchema={"type": "object", "properties": {}},
                    outputSchema={
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique identifier for the dataset",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Human-readable name of the dataset",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the dataset content",
                                },
                                "document_count": {
                                    "type": "integer",
                                    "description": "Number of documents in the dataset",
                                },
                                "chunk_count": {
                                    "type": "integer",
                                    "description": "Total number of chunks across all documents",
                                },
                                "embedding_count": {
                                    "type": "integer",
                                    "description": "Number of embeddings generated",
                                },
                                "tree_count": {
                                    "type": "integer",
                                    "description": "Number of RAPTOR trees built",
                                },
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "When the dataset was created",
                                },
                                "last_updated": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "When the dataset was last modified",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Current status of the dataset",
                                },
                                "total_tokens": {
                                    "type": "integer",
                                    "description": "Total number of tokens in the dataset",
                                },
                                "embedding_models": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of embedding models used",
                                },
                                "processing_status": {
                                    "type": "string",
                                    "description": "Current processing status",
                                },
                            },
                            "required": [
                                "id",
                                "name",
                                "description",
                                "document_count",
                                "created_at",
                                "last_updated",
                                "status",
                            ],
                        },
                    },
                ),
                # Add other tools as needed
            ]

        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "rag_retrieve":
                    result = await _rag_retrieve(
                        arguments["dataset_id"],
                        arguments["query"],
                        arguments.get("top_k", 5),
                        arguments.get("levels_cap"),
                        arguments.get("expand_k"),
                        arguments.get("reranker"),
                        arguments.get("score_threshold"),
                        container=self.container,
                    )
                    return [types.TextContent(type="text", text=str(result))]

                elif name == "list_datasets":
                    result = await _list_datasets(container=self.container)
                    return [types.TextContent(type="text", text=str(result))]

                # Add other tool implementations as needed
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        return server

    def get_mcp_server(self):
        """Get the MCP server instance"""
        return self.mcp_server

    async def run_stdio(self):
        """Run the MCP server over stdio"""
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream, write_stream, self.mcp_server.create_initialization_options()
            )


def initialize_mcp_with_container(container):
    """Initialize MCP tools with container for database connectivity"""
    service = RaptorMCPService(container)
    return service


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
        asyncio.run(mcp_instance.run_stdio())
    else:
        print(f"Starting RAPTOR MCP server on {args.host}:{args.port}...")
        # For HTTP mode, we now use the streamable version
        from .streamable_mcp_server import run_streamable_server

        asyncio.run(run_streamable_server(args.host, args.port))
