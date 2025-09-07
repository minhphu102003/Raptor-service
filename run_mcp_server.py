#!/usr/bin/env python3
"""
Standalone MCP Server for RAPTOR Service
This script runs an independent MCP server with pre-attached RAPTOR tools.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use absolute imports to avoid naming conflicts
from app.config import settings
from mcp_local.raptor_mcp_server import create_standalone_mcp_service


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

    async def async_main():
        try:
            # Create service with proper container for standalone usage
            service = create_standalone_mcp_service(db_dsn=orm_dsn, vector_dsn=vector_dsn)

            # Check if MCP is available
            from mcp.server.fastmcp import FastMCP

            print("MCP library is available")

            if len(sys.argv) > 1:
                if sys.argv[1] == "serve":
                    print("Starting RAPTOR MCP server on 127.0.0.1:3333...")
                    # Start the server
                    try:
                        await service.start_server()
                    except Exception as e:
                        print(f"Error starting server: {e}")
                elif sys.argv[1] == "stdio":
                    print("Starting RAPTOR MCP server in stdio mode...")
                    await service.run_stdio()
                else:
                    print(
                        "RAPTOR MCP Service ready. Use 'python run_mcp_server.py serve' to start server or 'python run_mcp_server.py stdio' for stdio mode."
                    )
            else:
                print(
                    "RAPTOR MCP Service ready. Use 'python run_mcp_server.py serve' to start server or 'python run_mcp_server.py stdio' for stdio mode."
                )

        except Exception as e:
            print(f"Failed to start standalone MCP service: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
