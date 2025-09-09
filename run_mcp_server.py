#!/usr/bin/env python3
"""
Standalone MCP Server for RAPTOR Service
This script runs an independent MCP server with pre-attached RAPTOR tools.
"""

import argparse
import asyncio
import logging
import os
import sys

# Set the event loop policy for Windows compatibility with psycopg
if sys.platform == "win32":
    from asyncio import WindowsSelectorEventLoopPolicy

    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
from app.logging_config import setup_logging

setup_logging()

# Configure logging for MCP
logging.getLogger("raptor.mcp").setLevel(logging.DEBUG)
logging.getLogger("raptor.mcp.streamable").setLevel(logging.DEBUG)

# Use absolute imports to avoid naming conflicts
from app.config import settings
from mcp_local.raptor_mcp_server import create_standalone_mcp_service
from mcp_local.streamable_mcp_server import create_streamable_mcp_service, run_streamable_server


def main():
    """Main entry point for the standalone MCP server."""
    # Get database connection strings from settings or environment
    orm_dsn = settings.pg_async_dsn or os.getenv("PG_ASYNC_DSN")
    vector_dsn = settings.vector.dsn or os.getenv("VECTOR_DSN")

    if not orm_dsn:
        print("Warning: No database DSN found. Using in-memory SQLite for demonstration.")
        orm_dsn = "sqlite+aiosqlite:///./raptor_mcp_demo.db"

    if not vector_dsn:
        print("Warning: No vector database DSN found. Using ORM database for vectors.")
        vector_dsn = orm_dsn

    print(f"Database DSN: {orm_dsn}")
    print(f"Vector DSN: {vector_dsn}")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3333)
    parser.add_argument("--path", default="/mcp")
    args = parser.parse_args()

    try:
        # Create service with proper container for standalone usage
        mcp_service = create_standalone_mcp_service(db_dsn=orm_dsn, vector_dsn=vector_dsn)

        print("RAPTOR MCP Service ready.")

        if args.mode == "stdio":
            print("Starting RAPTOR MCP server in stdio mode...")
            asyncio.run(mcp_service.run_stdio())
        else:
            print(f"Starting RAPTOR MCP server on {args.host}:{args.port}...")
            print(
                "According to MCP specification, the server provides a single endpoint that supports both GET and POST:"
            )
            print(
                f"  GET/POST http://{args.host}:{args.port}/mcp (Main MCP endpoint according to spec)"
            )
            print("")
            print("Legacy endpoints (for backward compatibility):")
            print(f"  GET  http://{args.host}:{args.port}/mcp/sse")
            print(f"  POST http://{args.host}:{args.port}/mcp/messages/")
            print("")
            print(f"  GET  http://{args.host}:{args.port}/health")
            print(f"  GET  http://{args.host}:{args.port}/routes")
            # Pass the container to the streamable server
            streamable_service = create_streamable_mcp_service(container=mcp_service.container)
            asyncio.run(streamable_service.start_server(args.host, args.port))

    except Exception as e:
        print(f"Failed to start standalone MCP service: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
