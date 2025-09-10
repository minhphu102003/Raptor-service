import asyncio
from contextlib import asynccontextmanager
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types
from starlette.routing import BaseRoute, Route
import uvicorn

from .middleware import log_all_requests
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

logger = logging.getLogger("raptor.mcp.streamable")


class StreamableMCPService:
    """Streamable MCP Service for RAPTOR functionality using standard MCP library"""

    def __init__(self, container=None):
        """Initialize streamable MCP service with optional container."""
        self.container = container
        self.sse_transport = SseServerTransport("/mcp")
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
                            "mode": {
                                "type": "string",
                                "enum": ["collapsed", "traversal"],
                                "default": "collapsed",
                            },
                            "levels_cap": {"type": "integer"},
                            "expand_k": {"type": "integer"},
                            "reranker": {"type": "boolean"},
                            "score_threshold": {"type": "number"},
                        },
                        "required": ["dataset_id", "query"],
                    },
                ),
                # Add other tools as needed
            ]

        @server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            try:
                logger.info(f"Call tool requested: {name}")
                logger.info(f"Arguments received: {arguments}")

                if name == "rag_retrieve":
                    # Log the specific arguments being passed to rag_retrieve
                    logger.info(f"rag_retrieve arguments: {arguments}")

                    result = await _rag_retrieve(
                        arguments["dataset_id"],
                        arguments["query"],
                        arguments.get("top_k", 5),
                        arguments.get("mode", "collapsed"),
                        arguments.get("levels_cap"),
                        arguments.get("expand_k"),
                        arguments.get("reranker"),
                        arguments.get("score_threshold"),
                        container=self.container,
                    )
                    return [types.TextContent(type="text", text=str(result))]

                # elif name == "list_datasets":
                #     result = await _list_datasets(container=self.container)
                #     return [types.TextContent(type="text", text=str(result))]

                # Add other tool implementations as needed
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        return server

    async def handle_sse_connection(self, scope, receive, send):
        """Handle SSE connection for the MCP server"""
        logger.info(f"Handling SSE connection: {scope.get('method')} {scope.get('path')}")
        logger.info(f"Headers: {dict(scope.get('headers', []))}")

        async with self.sse_transport.connect_sse(scope, receive, send) as (
            read_stream,
            write_stream,
        ):
            await self.mcp_server.run(
                read_stream, write_stream, self.mcp_server.create_initialization_options()
            )

    async def handle_post_message(self, scope, receive, send):
        """Handle POST messages for the MCP server"""
        logger.info(f"Handling POST message: {scope.get('method')} {scope.get('path')}")
        logger.info(f"Headers: {dict(scope.get('headers', []))}")

        await self.sse_transport.handle_post_message(scope, receive, send)

    async def handle_mcp_endpoint(self, scope, receive, send):
        """Handle the main MCP endpoint for both GET and POST according to MCP spec"""
        method = scope.get("method")
        logger.info(f"Handling MCP endpoint: {method} {scope.get('path')}")
        logger.info(f"Headers: {dict(scope.get('headers', []))}")

        if method == "GET":
            # Handle SSE connection
            logger.info("Handling GET request for SSE connection")
            async with self.sse_transport.connect_sse(scope, receive, send) as (
                read_stream,
                write_stream,
            ):
                await self.mcp_server.run(
                    read_stream, write_stream, self.mcp_server.create_initialization_options()
                )
        elif method == "POST":
            # Handle JSON-RPC message
            logger.info("Handling POST request for JSON-RPC message")
            await self.sse_transport.handle_post_message(scope, receive, send)
        else:
            # Return 405 Method Not Allowed
            logger.warning(f"Unsupported method: {method}")
            response_body = b"Method Not Allowed"
            await send(
                {
                    "type": "http.response.start",
                    "status": 405,
                    "headers": [
                        [b"content-type", b"text/plain"],
                        [b"content-length", str(len(response_body)).encode()],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": response_body,
                }
            )

    def mount_to_fastapi(self, app, path: str = "/mcp"):
        """Mount the streamable MCP server to a FastAPI application"""

        # Create handler classes as required by the MCP SDK
        class HandleSSE:
            def __init__(self, service):
                self.service = service

            async def __call__(self, scope, receive, send):
                await self.service.handle_sse_connection(scope, receive, send)

        class HandleMessages:
            def __init__(self, service):
                self.service = service

            async def __call__(self, scope, receive, send):
                await self.service.handle_post_message(scope, receive, send)

        # Create routes for SSE and messages
        routes: List[BaseRoute] = [
            Route(f"{path}/sse", endpoint=HandleSSE(self), methods=["GET"]),
            Route(f"{path}/messages", endpoint=HandleMessages(self), methods=["POST"]),
        ]

        # Create a FastAPI app with just these routes
        mcp_app = FastAPI(routes=routes)
        mcp_app.middleware("http")(log_all_requests)
        app.mount(path, mcp_app)
        logger.info(f"Streamable MCP server mounted to {path}")

    async def start_server(self, host: str = "127.0.0.1", port: int = 3333):
        """Start the streamable MCP server with proper MCP endpoint"""

        # Health check endpoint
        async def health_check(request):
            return {"status": "ok", "service": "RAPTOR MCP Server"}

        # Debug endpoint to show available routes
        async def show_routes(request):
            return {
                "available_endpoints": [
                    "GET  /health",
                    "GET  /routes",
                    "GET/POST /mcp (Main MCP endpoint according to spec)",
                    "GET  /mcp/sse (Legacy SSE endpoint)",
                    "POST /mcp/messages/ (Legacy Messages endpoint)",
                ]
            }

        # Create handler class for the main MCP endpoint
        class HandleMCP:
            def __init__(self, service):
                self.service = service

            async def __call__(self, scope, receive, send):
                await self.service.handle_mcp_endpoint(scope, receive, send)

        # Create routes
        routes: List[BaseRoute] = [
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/routes", endpoint=show_routes, methods=["GET"]),
            Route("/mcp", endpoint=HandleMCP(self), methods=["GET", "POST"]),  # Main MCP endpoint
            Route("/mcp/sse", endpoint=HandleMCP(self), methods=["GET"]),  # Legacy SSE endpoint
            Route(
                "/mcp/messages", endpoint=HandleMCP(self), methods=["POST"]
            ),  # Legacy Messages endpoint
        ]

        app = FastAPI(routes=routes)
        app.middleware("http")(log_all_requests)

        logger.info(f"Starting Streamable RAPTOR MCP server on {host}:{port}")
        logger.info("Available endpoints:")
        logger.info("  GET  /health")
        logger.info("  GET  /routes")
        logger.info("  GET/POST /mcp (Main MCP endpoint according to spec)")
        logger.info("  GET  /mcp/sse (Legacy SSE endpoint)")
        logger.info("  POST /mcp/messages/ (Legacy Messages endpoint)")
        config = uvicorn.Config(app, host=host, port=port, log_level="debug")
        server = uvicorn.Server(config)
        await server.serve()


def create_streamable_mcp_service(container=None):
    """Create a streamable MCP service for standalone usage or with container."""
    return StreamableMCPService(container)


# Example usage functions
async def run_streamable_server(host: str = "127.0.0.1", port: int = 3333, container=None):
    """Run the streamable MCP server standalone."""
    service = StreamableMCPService(container)
    await service.start_server(host, port)


if __name__ == "__main__":
    import argparse
    import sys

    # Set the event loop policy for Windows compatibility with psycopg
    if sys.platform == "win32":
        from asyncio import WindowsSelectorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3333)
    args = parser.parse_args()

    print(f"Starting Streamable RAPTOR MCP server on {args.host}:{args.port}...")
    print("Available endpoints:")
    print(f"  GET/POST http://{args.host}:{args.port}/mcp (Main MCP endpoint according to spec)")
    print(f"  GET  http://{args.host}:{args.port}/health")
    print(f"  GET  http://{args.host}:{args.port}/routes")
    print(f"  GET  http://{args.host}:{args.port}/mcp/sse (Legacy SSE endpoint)")
    print(f"  POST http://{args.host}:{args.port}/mcp/messages/ (Legacy Messages endpoint)")
    asyncio.run(run_streamable_server(args.host, args.port))
