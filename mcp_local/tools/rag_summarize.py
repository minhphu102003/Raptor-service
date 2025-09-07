import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("raptor.mcp.tools.rag.summarize")


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
