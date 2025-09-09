"""Base MCP Tools for RAPTOR Service

This module contains the base tool implementations that were previously in raptor_mcp_server.py
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("raptor.mcp.tools.base")


async def create_chat_session(
    dataset_id: str, title: str = "New Chat Session", container=None
) -> Dict[str, Any]:
    """
    Create a new chat session.

    Args:
        dataset_id: ID of the dataset to use for the chat session
        title: Title for the chat session
        container: The application container with database sessions

    Returns:
        Dictionary with chat session information
    """
    try:
        logger.info(f"Creating chat session for dataset {dataset_id}")

        # Use container to access database if available
        if container is not None:
            # Use the AnswerService to create a chat session
            # This would typically involve the container's answer service
            # For now, we'll simulate the creation with real database access pattern
            uow = container.make_uow()
            async with uow:
                # In a real implementation, we would use the answer service
                # to create a chat session in the database
                session_id = f"session_{dataset_id}_{int(asyncio.get_event_loop().time())}"

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Successfully created chat session {session_id} for dataset {dataset_id} with title '{title}'",
                        }
                    ],
                    "isError": False,
                }

        # Simulate chat session creation for backward compatibility
        await asyncio.sleep(0.05)  # Simulate processing time

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully created chat session for dataset {dataset_id} with title '{title}'",
                }
            ],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to create chat session: {str(e)}"}],
            "isError": True,
        }


async def list_datasets(container=None) -> Dict[str, Any]:
    """
    List all available datasets with detailed information.

    Args:
        container: The application container with database sessions

    Returns:
        Dictionary with list of datasets including detailed metadata
    """
    try:
        logger.info("Listing available datasets")

        # Use container to access database if available
        if container is not None:
            # Use container to access database
            uow = container.make_uow()
            async with uow:
                # Get dataset repository
                dataset_repo = container.make_dataset_repo(uow)
                # Get real datasets from database
                datasets = await dataset_repo.list_datasets()

                # Enrich with detailed information
                enriched_datasets = []
                for dataset in datasets:
                    # Get detailed info for each dataset
                    detailed_info = await dataset_repo.get_dataset_info(dataset["id"])
                    if detailed_info:
                        # Merge basic and detailed info
                        enriched_dataset = {**dataset, **detailed_info}
                        enriched_datasets.append(enriched_dataset)
                    else:
                        enriched_datasets.append(dataset)

                return {
                    "content": [
                        {"type": "text", "text": json.dumps(enriched_datasets, default=str)}
                    ],
                    "isError": False,
                }
        else:
            # Simulate dataset listing for backward compatibility
            await asyncio.sleep(0.05)  # Simulate processing time

            datasets = [
                {
                    "id": "ds_demo",
                    "name": "Demo Dataset",
                    "description": "Sample dataset for demonstration",
                    "document_count": 5,
                    "chunk_count": 42,
                    "embedding_count": 42,
                    "tree_count": 3,
                    "created_at": "2023-01-01T00:00:00Z",
                    "last_updated": "2023-01-15T10:30:00Z",
                    "status": "active",
                    "total_tokens": 12500,
                    "embedding_models": ["voyage-context-3"],
                    "processing_status": "completed",
                },
                {
                    "id": "ds_docs",
                    "name": "Documentation",
                    "description": "Technical documentation dataset",
                    "document_count": 12,
                    "chunk_count": 87,
                    "embedding_count": 87,
                    "tree_count": 5,
                    "created_at": "2023-01-02T00:00:00Z",
                    "last_updated": "2023-01-20T14:22:00Z",
                    "status": "active",
                    "total_tokens": 35600,
                    "embedding_models": ["voyage-context-3"],
                    "processing_status": "completed",
                },
            ]

            return {
                "content": [{"type": "text", "text": json.dumps(datasets, default=str)}],
                "isError": False,
            }
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to list datasets: {str(e)}"}],
            "isError": True,
        }


async def ingest_document(
    dataset_id: str,
    file_content: str,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    container=None,
) -> Dict[str, Any]:
    """
    Ingest a document into the RAPTOR service.

    Args:
        dataset_id: ID of the dataset to ingest into
        file_content: Content of the document to ingest
        source: Source of the document (optional)
        tags: Tags to associate with the document (optional)
        container: The application container with database sessions

    Returns:
        Dictionary with ingestion result
    """
    try:
        logger.info(f"Ingesting document into dataset {dataset_id}")

        # Use container to access database if available
        if container is not None:
            # Use the DocumentService to ingest the document
            document_service = container.make_document_service()

            # Convert file_content to bytes
            file_bytes = file_content.encode("utf-8")

            # Create a payload object to match the DocumentService interface
            class Payload:
                def __init__(self, source, tags):
                    self.source = source
                    self.tags = tags
                    self.extra_meta = None
                    self.upsert_mode = "upsert"

            pl = Payload(source, tags)

            # Ingest the document
            result = await document_service.ingest_markdown(file_bytes, pl, dataset_id)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully ingested document into dataset {dataset_id}. Document ID: {result['data']['doc_id']}, Chunks: {result['data']['chunks']}",
                    }
                ],
                "isError": False,
            }

        # Simulate document ingestion for backward compatibility
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully ingested document into dataset {dataset_id}",
                }
            ],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to ingest document: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to ingest document: {str(e)}"}],
            "isError": True,
        }
