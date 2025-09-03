"""
MCP Server for RAPTOR Service

This module implements the Model Context Protocol server that exposes
RAPTOR service functionality to AI agents.
"""

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast
from urllib.parse import quote

# Import tool implementations
from .tools.base_tools import create_chat_session, ingest_document, list_datasets
from .tools.document_tools import answer_question, retrieve_documents
from .tools.rag_tools import (
    rag_node_children,
    rag_node_get,
    rag_node_navigation,
    rag_path_to_root,
    rag_retrieve,
    rag_summarize,
)
from .tools.resources import read_resource

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

    def __init__(self, container=None):
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

        # RAG retrieve tool
        @self.mcp.tool()
        async def _rag_retrieve(
            dataset_id: str,
            query: str,
            top_k: int = 5,
            levels_cap: Optional[int] = None,
            expand_k: Optional[int] = None,
            reranker: Optional[bool] = None,
            score_threshold: Optional[float] = None,
        ) -> Dict[str, Any]:
            return await rag_retrieve(
                dataset_id, query, top_k, levels_cap, expand_k, reranker, score_threshold
            )

        # Node metadata tool
        @self.mcp.tool()
        async def _rag_node_get(node_id: str) -> Dict[str, Any]:
            return await rag_node_get(node_id)

        # Node children tool
        @self.mcp.tool()
        async def _rag_node_children(node_id: str) -> Dict[str, Any]:
            return await rag_node_children(node_id)

        # Node parent/siblings tool
        @self.mcp.tool()
        async def _rag_node_navigation(node_id: str, direction: str) -> Dict[str, Any]:
            return await rag_node_navigation(node_id, direction)

        # Path to root tool
        @self.mcp.tool()
        async def _rag_path_to_root(node_id: str) -> Dict[str, Any]:
            return await rag_path_to_root(node_id)

        # Summarize tool
        @self.mcp.tool()
        async def _rag_summarize(node_ids: List[str]) -> Dict[str, Any]:
            return await rag_summarize(node_ids)

        # Document ingestion tool (existing)
        @self.mcp.tool()
        async def _ingest_document(
            dataset_id: str,
            file_content: str,
            source: Optional[str] = None,
            tags: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            return await ingest_document(dataset_id, file_content, source, tags)

        # Document retrieval tool (existing)
        @self.mcp.tool()
        async def _retrieve_documents(
            dataset_id: str, query: str, mode: str = "collapsed", top_k: int = 5, expand_k: int = 3
        ) -> Dict[str, Any]:
            return await retrieve_documents(dataset_id, query, mode, top_k, expand_k)

        # Question answering tool (existing)
        @self.mcp.tool()
        async def _answer_question(
            dataset_id: str,
            query: str,
            mode: str = "collapsed",
            top_k: int = 5,
            temperature: float = 0.7,
        ) -> Dict[str, Any]:
            return await answer_question(dataset_id, query, mode, top_k, temperature)

        # Dataset management tool (existing)
        @self.mcp.tool()
        async def _list_datasets() -> Dict[str, Any]:
            return await list_datasets()

        # Chat session tool (existing)
        @self.mcp.tool()
        async def _create_chat_session(
            dataset_id: str, title: str = "New Chat Session"
        ) -> Dict[str, Any]:
            return await create_chat_session(dataset_id, title)

        logger.info("Registered RAPTOR MCP tools")

    def _register_resources(self):
        """Register all RAPTOR resources with the MCP server"""
        if not self.mcp:
            return

        # Resource reading handler
        @self.mcp.resource("raptor://{dataset_id}/nodes/{node_id}")
        async def _read_resource(uri: str) -> Dict[str, Any]:
            return await read_resource(uri)

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


# Create a global instance
raptor_mcp_service = RaptorMCPService()


if __name__ == "__main__":
    # Example of how to run the MCP server standalone
    if MCP_AVAILABLE:
        import asyncio
        import sys

        async def main():
            service = RaptorMCPService()
            if len(sys.argv) > 1 and sys.argv[1] == "serve":
                await service.start_server()
            else:
                print(
                    "RAPTOR MCP Service ready. Use 'python raptor_mcp_server.py serve' to start server."
                )

        asyncio.run(main())
    else:
        print("MCP not available. Install with: pip install mcp[cli]")
