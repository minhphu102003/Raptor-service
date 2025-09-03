"""
Example MCP (Model Control Protocol) Server Implementation

This is a simple FastAPI implementation of an MCP server that can be used
as a reference for implementing remote model services.
"""

import json
import os

# Use secrets module for cryptographically secure random numbers
import secrets
import time
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="MCP Example Server", version="1.0.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Dict[str, int]] = None


@app.post("/v1/chat/completions", response_model=Union[ChatCompletionResponse, str])
async def chat_completions(request: ChatCompletionRequest):
    """
    Example chat completion endpoint that simulates a remote LLM service.
    In a real implementation, this would call an actual LLM.
    """
    try:
        # Use secrets for cryptographically secure random numbers
        # For simulation purposes, we can use a deterministic approach
        # or just a simple time-based approach for demo purposes
        time.sleep(0.1 + (hash(request.model) % 40) / 100.0)  # nosec B311

        # Extract the last user message for simulation
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        last_user_message = user_messages[-1].content if user_messages else ""

        # Generate a simulated response
        simulated_response = (
            f"Simulated response from MCP model '{request.model}' to: {last_user_message[:50]}..."
        )

        if request.stream:
            # For streaming, return a simple string (in reality this would be an SSE stream)
            return (
                f"data: {json.dumps({'choices': [{'delta': {'content': simulated_response}}]})}\n\n"
            )

        # For non-streaming, return a proper completion response
        response = ChatCompletionResponse(
            id="mcp-" + str(hash(request.model + last_user_message))[:10],
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=simulated_response),
                    finish_reason="stop",
                )
            ],
            usage={
                "prompt_tokens": len(last_user_message.split()),
                "completion_tokens": len(simulated_response.split()),
                "total_tokens": len(last_user_message.split()) + len(simulated_response.split()),
            },
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {"id": "mcp-llama-3-70b", "object": "model", "created": 1677610602, "owned_by": "mcp"},
            {"id": "mcp-mistral-7b", "object": "model", "created": 1677610602, "owned_by": "mcp"},
        ],
    }


if __name__ == "__main__":
    # Bind to localhost instead of all interfaces for security
    uvicorn.run(app, host="127.0.0.1", port=8001)
