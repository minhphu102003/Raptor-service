import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("raptor.mcp.tools.rag.navigation")


async def rag_path_to_root(node_id: str, container=None) -> Dict[str, Any]:
    """
    Get the path from a node to the root of the tree.

    Args:
        node_id: ID of the starting node
        container: Container with database connectivity (optional for backward compatibility)

    Returns:
        Path from node to root with summaries at each level
    """
    try:
        logger.info(f"Getting path to root for node {node_id}")

        # If container is provided, use real database connectivity
        if container is not None:
            # Use unit of work pattern to get repository
            async with container.make_uow() as uow:
                retrieval_repo = container.make_retrieval_repo(uow)

                # Get the path to root from database
                path_data = await retrieval_repo.get_path_to_root(node_id=node_id)

                # Format the path data
                path_items = []
                for node in path_data:
                    path_items.append(
                        {
                            "id": node["node_id"],
                            "level": node["level"],
                            "kind": node["kind"],
                            "text": node["text"],
                        }
                    )

                # Create a readable path representation
                path_text = " -> ".join([f"{node['kind']}({node['id']})" for node in path_items])
        else:
            # Simulate path to root retrieval for backward compatibility
            await asyncio.sleep(0.05)  # Simulate processing time

            # Generate simulated path
            path = [f"level_{i}_summary_for_{node_id}" for i in range(3)]
            path.append("root_summary")
            path_text = " -> ".join(path)

        return {
            "content": [{"type": "text", "text": f"Path to root: {path_text}"}],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to get path to root: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to get path to root: {str(e)}"}],
            "isError": True,
        }
