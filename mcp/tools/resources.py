"""Resource Handlers for RAPTOR MCP Service

This module contains resource handling implementations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger("raptor.mcp.resources")


async def read_resource(uri: str, container=None) -> Dict[str, Any]:
    """
    Read a RAPTOR resource with real database connectivity.

    Args:
        uri: URI of the resource to read
        container: The application container with database sessions (optional for backward compatibility)

    Returns:
        Resource content
    """
    try:
        logger.info(f"Reading resource: {uri}")

        # Parse the URI to determine what to return
        if uri.startswith("raptor://"):
            # Extract dataset and node info from URI
            parsed_uri = urlparse(uri)
            path_parts = parsed_uri.path.strip("/").split("/")

            if len(path_parts) >= 2 and path_parts[0] == "nodes":
                dataset_id = parsed_uri.netloc
                node_id = path_parts[1]

                # If container is provided, use real database connectivity
                if container is not None:
                    # Use container to access database
                    uow = container.make_uow()
                    async with uow:
                        # Get retrieval repository
                        retrieval_repo = container.make_retrieval_repo(uow)

                        # Get node metadata and content
                        node_data = await retrieval_repo.get_node_metadata(node_id=node_id)

                        if node_data is None:
                            raise Exception(f"Node {node_id} not found in dataset {dataset_id}")

                        content = node_data.get("text", "")

                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "text/plain",
                                    "text": content
                                    or f"Content of node {node_id} from dataset {dataset_id}",
                                }
                            ]
                        }
                else:
                    # Fallback to simulated response if no container provided (backward compatibility)
                    await asyncio.sleep(0.05)  # Simulate processing time

                    content = (
                        f"Content of node {node_id} from dataset {dataset_id}. "
                        f"This is the detailed content that would be retrieved from the database."
                    )

                    return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]}

        # Default response for unrecognized URIs
        return {
            "contents": [
                {"uri": uri, "mimeType": "text/plain", "text": f"Resource content for {uri}"}
            ]
        }
    except Exception as e:
        logger.error(f"Failed to read resource {uri}: {e}")
        raise Exception(f"Failed to read resource: {str(e)}")
