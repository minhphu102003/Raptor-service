import asyncio
import logging
from typing import Any, Dict, List, Optional

from services import (
    FPTLLMClient,
    QueryRewriteService,
    RetrievalService,
    RetrieveBody,
    VoyageEmbeddingClientAsync,
)

logger = logging.getLogger("raptor.mcp.tools.rag")


async def rag_retrieve(
    dataset_id: str,
    query: str,
    top_k: int = 5,
    levels_cap: Optional[int] = None,
    expand_k: Optional[int] = None,
    reranker: Optional[bool] = None,
    score_threshold: Optional[float] = None,
    container=None,
) -> Dict[str, Any]:
    """
    Retrieve top-K nodes/chunks based on a query.

    Args:
        dataset_id: ID of the dataset to search
        query: Search query
        top_k: Number of top results to return (default: 5)
        levels_cap: Maximum tree levels to traverse
        expand_k: Number of nodes to expand (for collapsed mode)
        reranker: Whether to use a reranker
        score_threshold: Minimum score threshold for results
        container: The application container with database sessions

    Returns:
        List of ContentBlocks with resource links and structured content
    """
    try:
        logger.info(f"Retrieving documents from dataset {dataset_id} for query: {query}")

        if container is None:
            raise ValueError("Container is required for database access")

        # Initialize services needed for retrieval
        fpt_client = FPTLLMClient(model="DeepSeek-V3")
        voyage_client = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)
        rewrite_svc = QueryRewriteService(fpt_client=fpt_client)
        retrieval_svc = RetrievalService(rewrite_svc=rewrite_svc, embed_svc=voyage_client)

        # Create the retrieval body
        retrieve_body = RetrieveBody(
            dataset_id=dataset_id,
            query=query,
            mode="collapsed" if expand_k is not None else "traversal",
            top_k=top_k,
            expand_k=expand_k or 5,
            levels_cap=levels_cap or 0,
            use_reranker=reranker or False,
        )

        # Use container to access database
        uow = container.make_uow()
        async with uow:
            repo = container.make_retrieval_repo(uow)
            result = await retrieval_svc.retrieve(retrieve_body, repo=repo)

            if result.get("code") != 200:
                raise Exception(f"Retrieval failed: {result.get('message', 'Unknown error')}")

            chunks = result.get("data", [])

            # Convert chunks to resource format
            results = []
            for i, chunk in enumerate(chunks):
                # Create a resource URI for the chunk
                resource_uri = f"raptor://{dataset_id}/nodes/{chunk.get('chunk_id', f'chunk_{i}')}"
                results.append(
                    {
                        "type": "resource",
                        "resource": {
                            "uri": resource_uri,
                            "mimeType": "text/plain",
                            "text": chunk.get("text", ""),
                            "metadata": {
                                "score": chunk.get("dist", 1.0),
                                "chunk_id": chunk.get("chunk_id", ""),
                                "doc_id": chunk.get("doc_id", ""),
                            },
                        },
                    }
                )

            return {"content": results, "isError": False}
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to retrieve documents: {str(e)}"}],
            "isError": True,
        }


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


async def rag_summarize(node_ids: List[str], container=None) -> Dict[str, Any]:
    """
    Summarize selected nodes.

    Args:
        node_ids: List of node IDs to summarize
        container: Container with database connectivity (optional for backward compatibility)

    Returns:
        Combined summary of the selected nodes
    """
    try:
        logger.info(f"Summarizing nodes: {node_ids}")

        # If container is provided, use real database connectivity
        if container is not None:
            # Use unit of work pattern to get repositories
            async with container.make_uow() as uow:
                retrieval_repo = container.make_retrieval_repo(uow)

                # Get node texts from database
                node_data = await retrieval_repo.get_node_texts_by_ids(node_ids=node_ids)

                if not node_data:
                    return {
                        "content": [{"type": "text", "text": "No nodes found to summarize."}],
                        "isError": False,
                    }

                # Extract texts from node data
                texts = [node["text"] for node in node_data if node["text"]]

                if not texts:
                    return {
                        "content": [
                            {"type": "text", "text": "No text content found in the selected nodes."}
                        ],
                        "isError": False,
                    }

                # Create a default LLM for summarization
                from services.clustering.summarizer import LLMSummarizer, make_llm
                from services.config import get_service_config
                from services.config.model_config import LLMProvider

                config = get_service_config().model_config
                # Use the get_default_model method to get the default FPT model
                default_model = config.get_default_model(LLMProvider.FPT)
                llm = make_llm(default_model, config)
                summarizer = LLMSummarizer(llm, config)

                # Generate summary using the LLM
                try:
                    summary_text = await summarizer.summarize_cluster(texts)
                except Exception as e:
                    logger.error(f"Failed to generate summary with LLM: {e}")
                    # Fallback to simple concatenation if LLM fails
                    summary_text = "Summary of nodes:\n\n" + "\n\n".join(
                        texts[:5]
                    )  # Limit to 5 nodes

                return {
                    "content": [{"type": "text", "text": summary_text}],
                    "isError": False,
                }
        else:
            # Simulate summarization for backward compatibility
            await asyncio.sleep(0.2)  # Simulate processing time

            # Generate simulated summary
            summary = (
                f"This is a combined summary of nodes: {', '.join(node_ids)}. "
                f"The key points discussed are: 1) Important concept A, 2) Key idea B, "
                f"3) Relevant detail C. This summary provides a comprehensive overview "
                f"of the information contained in these nodes."
            )

            return {"content": [{"type": "text", "text": summary}], "isError": False}
    except Exception as e:
        logger.error(f"Failed to summarize nodes: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to summarize nodes: {str(e)}"}],
            "isError": True,
        }
