import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("raptor.mcp.tools.rag.node")


async def rag_node_get(node_id: str, container) -> Dict[str, Any]:
    """
    Get metadata and summary of a node.

    Args:
        node_id: ID of the node to retrieve
        container: The application container with database sessions (required)

    Returns:
        Node metadata including id, level, parent, children_count, doc spans
    """
    try:
        logger.info(f"Getting metadata for node {node_id}")

        # Check if container is provided
        if container is None:
            raise ValueError("Container is required for database access")

        # Use container to access database
        uow = container.make_uow()
        async with uow:
            repo = container.make_retrieval_repo(uow)
            node_data = await repo.get_node_metadata(node_id=node_id)

            if node_data is None:
                raise Exception(f"Node {node_id} not found")

            # Format the response
            metadata = {
                "id": node_data["node_id"],
                "level": node_data["level"],
                "parent": node_data["parent_id"],
                "children_count": node_data["children_count"],
                "dataset_id": node_data["dataset_id"],
                "kind": node_data["kind"],
                "text": node_data["text"],
                "meta": node_data["meta"],
            }

            return {
                "content": [{"type": "text", "text": f"Node metadata: {metadata}"}],
                "isError": False,
            }
    except Exception as e:
        logger.error(f"Failed to get node metadata: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to get node metadata: {str(e)}"}],
            "isError": True,
        }


async def rag_node_children(node_id: str, container=None) -> Dict[str, Any]:
    """
    List child nodes of a given node.

    Args:
        node_id: ID of the parent node
        container: The application container with database sessions

    Returns:
        List of child nodes
    """
    try:
        logger.info(f"Getting children for node {node_id}")

        if container is None:
            # Fallback to simulated response if no container provided
            await asyncio.sleep(0.05)  # Simulate processing time

            # Generate simulated children
            children = [f"child_{i}_of_{node_id}" for i in range(3)]

            return {
                "content": [{"type": "text", "text": f"Child nodes: {children}"}],
                "isError": False,
            }

        # Use container to access database
        uow = container.make_uow()
        async with uow:
            repo = container.make_retrieval_repo(uow)
            children_data = await repo.get_node_children(node_id=node_id)

            # Format the response
            children_list = []
            for child in children_data:
                children_list.append(
                    {
                        "id": child["node_id"],
                        "level": child["level"],
                        "kind": child["kind"],
                        "text": child["text"],
                    }
                )

            return {
                "content": [{"type": "text", "text": f"Child nodes: {children_list}"}],
                "isError": False,
            }
    except Exception as e:
        logger.error(f"Failed to get node children: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to get node children: {str(e)}"}],
            "isError": True,
        }


async def rag_node_navigation(node_id: str, direction: str, container=None) -> Dict[str, Any]:
    """
    Navigate to parent or siblings of a node.

    Args:
        node_id: ID of the node to navigate from
        direction: Direction to navigate ("parent" or "siblings")
        container: Container with database connectivity (optional for backward compatibility)

    Returns:
        Parent node or sibling nodes
    """
    try:
        logger.info(f"Navigating {direction} from node {node_id}")

        # If container is provided, use real database connectivity
        if container is not None:
            # Use unit of work pattern to get repository
            async with container.make_uow() as uow:
                retrieval_repo = container.make_retrieval_repo(uow)

                if direction == "parent":
                    parent_data = await retrieval_repo.get_node_parent(node_id=node_id)
                    if parent_data:
                        result = {
                            "id": parent_data["node_id"],
                            "level": parent_data["level"],
                            "kind": parent_data["kind"],
                            "text": parent_data["text"],
                        }
                    else:
                        result = None
                elif direction == "siblings":
                    siblings_data = await retrieval_repo.get_node_siblings(node_id=node_id)
                    result = []
                    for sibling in siblings_data:
                        result.append(
                            {
                                "id": sibling["node_id"],
                                "level": sibling["level"],
                                "kind": sibling["kind"],
                                "text": sibling["text"],
                            }
                        )
                else:
                    raise ValueError(f"Invalid direction: {direction}")
        else:
            # Simulate navigation for backward compatibility
            await asyncio.sleep(0.05)  # Simulate processing time

            if direction == "parent":
                result = f"parent_of_{node_id}"
            elif direction == "siblings":
                result = [f"sibling_{i}_of_{node_id}" for i in range(2)]
            else:
                raise ValueError(f"Invalid direction: {direction}")

        return {
            "content": [{"type": "text", "text": f"{direction.capitalize()}: {result}"}],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to navigate node: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to navigate node: {str(e)}"}],
            "isError": True,
        }
