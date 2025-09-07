"""
SSE Endpoint for MCP Server

This module provides Server-Sent Events (SSE) support for the MCP server,
allowing AI agents to communicate with the RAPTOR service in real-time.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("raptor.mcp.sse")


class SSEManager:
    """Manager for SSE connections"""

    def __init__(self):
        self.connections: Dict[str, asyncio.Queue] = {}
        self.connection_counter = 0

    async def connect(self) -> tuple[str, asyncio.Queue]:
        """Create a new SSE connection"""
        connection_id = f"conn_{self.connection_counter}"
        self.connection_counter += 1

        queue = asyncio.Queue()
        self.connections[connection_id] = queue

        logger.info(f"SSE connection established: {connection_id}")
        return connection_id, queue

    def disconnect(self, connection_id: str):
        """Remove a connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"SSE connection closed: {connection_id}")

    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send a message to a specific connection"""
        if connection_id in self.connections:
            await self.connections[connection_id].put(message)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Send a message to all connections"""
        for queue in self.connections.values():
            await queue.put(message)


# Global SSE manager
sse_manager = SSEManager()

# Create router for SSE endpoints
sse_router = APIRouter(prefix="/mcp", tags=["mcp"])


@sse_router.get("/sse")
async def sse_endpoint(request: Request) -> StreamingResponse:
    """
    Server-Sent Events endpoint for MCP communication.

    This endpoint allows AI agents to connect to the RAPTOR service
    using the Model Context Protocol over SSE.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        # Create a new connection
        connection_id, queue = await sse_manager.connect()

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'connection_id': connection_id})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Format as SSE message
                    yield f"data: {json.dumps(message)}\n\n"

                    # Special handling for close messages
                    if message.get("type") == "close":
                        break

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE connection {connection_id}: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break

        finally:
            # Clean up connection
            sse_manager.disconnect(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",  # nosec B104 - This is for local development
        },
    )


@sse_router.post("/messages")
async def send_message(message: Dict[str, Any]) -> Dict[str, str]:
    """
    Send a message to all connected SSE clients.

    Args:
        message: Message to send to clients

    Returns:
        Confirmation response
    """
    await sse_manager.broadcast_message(message)
    return {"status": "message_sent"}


@sse_router.get("/connections")
async def list_connections() -> Dict[str, Any]:
    """
    List all active SSE connections.

    Returns:
        Dictionary with connection information
    """
    return {
        "connections": list(sse_manager.connections.keys()),
        "count": len(sse_manager.connections),
    }


# Example usage functions
async def send_tool_result(connection_id: str, tool_call_id: str, result: Dict[str, Any]):
    """Send a tool result back to a specific client"""
    message = {"type": "tool_result", "tool_call_id": tool_call_id, "result": result}
    await sse_manager.send_message(connection_id, message)


async def send_progress_update(connection_id: str, progress: float, message: str = ""):
    """Send a progress update to a specific client"""
    update_message = {"type": "progress", "progress": progress, "message": message}
    await sse_manager.send_message(connection_id, update_message)


# Integration with FastAPI app
def mount_sse_endpoints(app):
    """Mount SSE endpoints to a FastAPI application"""
    app.include_router(sse_router)
    logger.info("SSE endpoints mounted to FastAPI app")
