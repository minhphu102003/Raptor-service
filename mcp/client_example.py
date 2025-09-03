"""
MCP Client Example for RAPTOR Service

This module demonstrates how to create an MCP client that can connect to
the RAPTOR service and use its tools.
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict

import aiohttp


class RaptorMCPClient:
    """Client for connecting to the RAPTOR MCP service"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session: aiohttp.ClientSession | None = None
        self.connection_id: str | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def connect_sse(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Connect to the SSE endpoint and yield messages.

        Yields:
            Dictionary messages from the server
        """
        if not self.session:
            raise RuntimeError("Client must be used as async context manager")

        async with self.session.get(f"{self.base_url}/mcp/sse") as response:
            async for line in response.content:
                if line.startswith(b"data: "):
                    data = line[6:].strip()
                    if data:
                        try:
                            message = json.loads(data.decode("utf-8"))
                            if message.get("type") == "connected":
                                self.connection_id = message.get("connection_id")
                            yield message
                        except json.JSONDecodeError:
                            print(f"Failed to parse message: {data}")

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a tool on the RAPTOR service.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments for the tool

        Returns:
            Tool result
        """
        # In a real implementation, this would send a tool call message
        # over the SSE connection or use a direct API endpoint
        print(f"Calling tool '{tool_name}' with args: {kwargs}")

        # Simulate tool call result
        await asyncio.sleep(0.5)

        if tool_name == "ingest_document":
            return {
                "status": "success",
                "dataset_id": kwargs.get("dataset_id"),
                "document_id": "doc_12345",
                "message": "Document ingested successfully",
            }
        elif tool_name == "retrieve_documents":
            return {
                "status": "success",
                "query": kwargs.get("query"),
                "results": [
                    {"id": "doc_1", "content": "First relevant document"},
                    {"id": "doc_2", "content": "Second relevant document"},
                ],
            }
        elif tool_name == "answer_question":
            return {
                "status": "success",
                "query": kwargs.get("query"),
                "answer": "This is the answer to your question based on the relevant documents.",
                "context": [
                    {"doc_id": "doc_1", "relevance": 0.95},
                    {"doc_id": "doc_2", "relevance": 0.87},
                ],
            }
        elif tool_name == "list_datasets":
            return {
                "status": "success",
                "datasets": [
                    {"id": "ds_demo", "name": "Demo Dataset"},
                    {"id": "ds_docs", "name": "Documentation"},
                ],
            }
        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}


# Example usage
async def main():
    """Example of using the RAPTOR MCP client"""
    async with RaptorMCPClient() as client:
        print("Connecting to RAPTOR MCP service...")

        # Start SSE connection in background
        async def listen_for_messages():
            try:
                async for message in client.connect_sse():
                    print(f"Received message: {message}")
            except Exception as e:
                print(f"Error in SSE connection: {e}")

        # Start listening for messages
        listen_task = asyncio.create_task(listen_for_messages())

        # Wait a moment for connection to establish
        await asyncio.sleep(1)

        # Call some tools
        print("\n--- Calling tools ---")

        # List datasets
        result = await client.call_tool("list_datasets")
        print(f"List datasets result: {result}")

        # Ingest a document
        result = await client.call_tool(
            "ingest_document",
            dataset_id="ds_demo",
            file_content="This is a sample document content for ingestion.",
        )
        print(f"Ingest document result: {result}")

        # Retrieve documents
        result = await client.call_tool(
            "retrieve_documents", dataset_id="ds_demo", query="sample query"
        )
        print(f"Retrieve documents result: {result}")

        # Answer a question
        result = await client.call_tool(
            "answer_question", dataset_id="ds_demo", query="What is this about?"
        )
        print(f"Answer question result: {result}")

        # Wait a bit to receive any remaining messages
        await asyncio.sleep(2)

        # Cancel the listening task
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
