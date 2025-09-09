"""
Example usage of the RAPTOR MCP Service

This script demonstrates how to use the RAPTOR MCP service with a FastAPI application.
"""

import asyncio

from fastapi import FastAPI

from mcp_local.raptor_mcp_server import RaptorMCPService, create_standalone_mcp_service
from mcp_local.streamable_mcp_server import StreamableMCPService, create_streamable_mcp_service


# Example 1: Integration with FastAPI application
def integrate_with_fastapi():
    """
    Example of how to integrate the MCP service with a FastAPI application.

    In your main FastAPI application file:
    """
    # This is pseudocode to show the integration pattern
    app = FastAPI()

    # Assuming you have a container with database connectivity
    # app.state.container = your_container

    # Create MCP service with your container
    # mcp_service = RaptorMCPService(container=app.state.container)

    # Get the MCP server instance
    # mcp_server = mcp_service.get_mcp_server()

    print("MCP service integrated with FastAPI application")


# Example 2: Standalone usage
async def standalone_usage():
    """
    Example of how to use the MCP service in standalone mode.
    """
    try:
        # Create service with database connection strings
        # Replace with your actual database connection strings
        mcp_service = create_standalone_mcp_service(
            db_dsn="postgresql://user:password@localhost:5432/db",
            vector_dsn="postgresql://user:password@localhost:5432/vector_db",
        )

        print("Standalone MCP service created successfully")

        # You can now use the service
        # mcp_server = mcp_service.get_mcp_server()

    except Exception as e:
        print(f"Failed to create standalone MCP service: {e}")


# Example 3: Using MCP tools directly
async def use_mcp_tools():
    """
    Example of how to use MCP tools directly in your application code.
    """
    try:
        from mcp_local.tools import create_chat_session, list_datasets, rag_retrieve

        # These would normally be called by an AI assistant through the MCP protocol
        # But you can also call them directly in your application code

        # List datasets (without container - will return simulated data)
        datasets_result = await list_datasets()
        print(f"Datasets: {datasets_result}")

        # Create chat session (without container - will return simulated data)
        chat_result = await create_chat_session("my_dataset", "My Chat Session")
        print(f"Chat session: {chat_result}")

    except Exception as e:
        print(f"Error using MCP tools: {e}")


# Example 4: Running the MCP server
async def run_mcp_server():
    """
    Example of how to run the MCP server standalone.
    """
    try:
        # Create service with proper container for standalone usage
        service = create_standalone_mcp_service()

        print("Starting RAPTOR MCP server...")
        print("RAPTOR MCP Service ready. Connect your AI assistant to use the tools.")

        # In a real implementation, you would start the server here
        # await service.run_stdio()

    except Exception as e:
        print(f"Failed to start standalone MCP service: {e}")


# Example 5: Running the Streamable MCP server
async def run_streamable_mcp_server():
    """
    Example of how to run the Streamable MCP server standalone.
    """
    try:
        # Create streamable service
        service = create_streamable_mcp_service()

        print("Starting Streamable RAPTOR MCP server...")
        print("Streamable RAPTOR MCP Service ready. Connect your AI assistant to use the tools.")

        # In a real implementation, you would start the server here
        # await service.start_server()

    except Exception as e:
        print(f"Failed to start streamable MCP service: {e}")


if __name__ == "__main__":
    print("RAPTOR MCP Service Usage Examples")
    print("=" * 40)

    # Example 1
    integrate_with_fastapi()

    print("\n" + "=" * 40)

    # Example 2
    print("Example 2: Standalone usage")
    asyncio.run(standalone_usage())

    print("\n" + "=" * 40)

    # Example 3
    print("Example 3: Using MCP tools directly")
    asyncio.run(use_mcp_tools())

    print("\n" + "=" * 40)

    # Example 4
    print("Example 4: Running the MCP server")
    asyncio.run(run_mcp_server())

    print("\n" + "=" * 40)

    # Example 5
    print("Example 5: Running the Streamable MCP server")
    asyncio.run(run_streamable_mcp_server())
