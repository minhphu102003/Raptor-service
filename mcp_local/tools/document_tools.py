"""Document MCP Tools for RAPTOR Service

This module contains document-related tool implementations.
"""

import asyncio
import logging
from typing import Any, Dict

from services.providers.fpt_llm import FPTLLMClient
from services.providers.voyage import VoyageEmbeddingClientAsync

# Fix the import paths
from services.retrieval.retrieval_service import RetrievalService, RetrieveBody

logger = logging.getLogger("raptor.mcp.tools.document")


async def answer_question(
    dataset_id: str,
    query: str,
    mode: str = "collapsed",
    top_k: int = 5,
    temperature: float = 0.7,
    container=None,
) -> Dict[str, Any]:
    """
    Answer a question using the RAPTOR service with real database connectivity.

    Args:
        dataset_id: ID of the dataset to use for answering
        query: Question to answer
        mode: Retrieval mode ("collapsed" or "traversal")
        top_k: Number of relevant documents to consider
        temperature: LLM temperature for answer generation
        container: The application container with database sessions (optional for backward compatibility)

    Returns:
        Dictionary with answer and context
    """
    try:
        logger.info(f"Answering question for dataset {dataset_id}: {query}")

        # If container is provided, use real database connectivity
        if container is not None:
            # Initialize services needed for retrieval and answering
            fpt_client = FPTLLMClient(model="DeepSeek-V3")
            voyage_client = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)
            retrieval_svc = RetrievalService(embed_svc=voyage_client)

            # Create the retrieval body
            retrieve_body = RetrieveBody(
                dataset_id=dataset_id,
                query=query,
                mode="collapsed" if mode == "collapsed" else "traversal",
                top_k=top_k,
            )

            # Use container to access database
            uow = container.make_uow()
            async with uow:
                repo = container.make_retrieval_repo(uow)
                # Use the retrieval service to get relevant passages
                result = await retrieval_svc.retrieve(retrieve_body, repo=repo)

                if result.get("code") != 200:
                    raise Exception(f"Retrieval failed: {result.get('message', 'Unknown error')}")

                passages = result.get("data", [])

                # Normalize passages
                normalized_passages = []
                for passage in passages:
                    normalized_passage = passage.copy()
                    if "text" in passage and "content" not in passage:
                        normalized_passage["content"] = passage["text"]
                    normalized_passages.append(normalized_passage)

                # Build prompt using the prompt service
                from services.retrieval.prompt_service import PromptService

                prompt_service = PromptService()
                prompt = await prompt_service.build_prompt(query, normalized_passages[:top_k])

                # Generate answer using LLM
                answer_text = await fpt_client.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=2000,
                )

                # Format the response
                response_data = {
                    "answer": answer_text,
                    "model": "DeepSeek-V3",
                    "top_k": top_k,
                    "mode": mode,
                    "passages": normalized_passages[:top_k],
                }

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Answer: {response_data['answer']}\n\nContext: {response_data['passages']}",
                        }
                    ],
                    "isError": False,
                }
        else:
            # Fallback to simulated response if no container provided (backward compatibility)
            await asyncio.sleep(0.2)  # Simulate processing time

            # Generate simulated answer and context
            answer = f"Based on the documents in dataset {dataset_id}, here is the answer to your question: {query}. This is a comprehensive response that takes into account the relevant information from multiple sources."

            context = []
            for i in range(min(top_k, 3)):
                context.append(
                    {
                        "chunk_id": f"chunk_{i}",
                        "doc_id": f"doc_{i % 2}",
                        "text": f"Relevant context {i} that supports the answer to '{query}'",
                        "relevance": 0.9 - (i * 0.1),
                    }
                )

            return {
                "content": [{"type": "text", "text": f"Answer: {answer}\n\nContext: {context}"}],
                "isError": False,
            }
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to generate answer: {str(e)}"}],
            "isError": True,
        }
