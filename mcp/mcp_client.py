import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

import aiohttp

from services.providers.model_registry import ModelRegistry

logger = logging.getLogger("raptor.mcp")


class MCPClient:
    """Client for communicating with remote Model Control Protocol services"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """Send chat completion request to remote MCP service"""
        if not self.session:
            raise RuntimeError("MCPClient must be used as async context manager")

        payload = {
            "model": model,
            "messages": messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stream:
            payload["stream"] = True

        url = f"{self.base_url}/v1/chat/completions"
        headers = self._get_headers()

        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    if stream:
                        # For streaming, return the response text
                        return await response.text()
                    else:
                        return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"MCP request failed with status {response.status}: {error_text}")
                    raise Exception(f"MCP request failed: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Failed to communicate with MCP service: {e}")
            raise


class MCPModelAdapter:
    """Adapter to integrate MCP models with the existing model registry"""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def chat_completions(self, **kwargs):
        """Wrapper for MCP chat completions"""
        return await self.mcp_client.chat_completions(**kwargs)

    async def summarize(
        self, prompt: str, *, max_tokens: int, temperature: float, model: str
    ) -> str:
        """Summarization using MCP service"""
        messages = [
            {
                "role": "system",
                "content": """
                You are a concise, faithful summarizer.
                Output ONLY the final summary as plain text (no headings, no labels, no lists, no JSON/HTML/Markdown).
                Do NOT include chain-of-thought or reasoning markers.
                If information is uncertain, write "unknown".
                Preserve factual entities, numbers, and dates from the source.
                """,
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.mcp_client.chat_completions(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            if isinstance(response, dict) and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise ValueError(f"Unexpected response format from MCP: {type(response)}")

        except Exception as e:
            logger.error(f"Failed to summarize with MCP: {e}")
            raise
