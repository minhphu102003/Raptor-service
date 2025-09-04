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

logger = logging.getLogger("raptor.mcp.tools.rag.retrieve")


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
