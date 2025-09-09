"""
Middleware for the MCP server.
"""

import json
import logging
from typing import Any, Dict

from fastapi import Request
from starlette.responses import Response

logger = logging.getLogger("raptor.mcp.middleware")


async def log_all_requests(request: Request, call_next):
    """Middleware to log all incoming requests"""
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")

    # Log request body for POST requests
    if request.method == "POST":
        try:
            body = await request.body()
            body_str = body.decode()
            logger.info(f"Request body: {body_str}")

            # Parse and filter out null values from JSON-RPC requests
            try:
                body_json = json.loads(body_str)
                if isinstance(body_json, dict) and body_json.get("method") == "tools/call":
                    # Filter out null values from arguments
                    if "params" in body_json and "arguments" in body_json["params"]:
                        original_args = body_json["params"]["arguments"]
                        filtered_args = {k: v for k, v in original_args.items() if v is not None}
                        body_json["params"]["arguments"] = filtered_args
                        logger.info(
                            f"Filtered null values from arguments. Before: {original_args}, After: {filtered_args}"
                        )
                        # Update the request body
                        request._body = json.dumps(body_json).encode()
            except json.JSONDecodeError:
                pass  # Not a JSON request, continue normally
        except Exception as e:
            logger.info(f"Could not read request body: {e}")

    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
