"""Base MCP Tools for RAPTOR Service

This module contains the base tool implementations that were previously in raptor_mcp_server.py
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("raptor.mcp.tools.base")


async def list_datasets(container=None) -> Dict[str, Any]:
    """
    List all available datasets.

    Args:
        container: The application container with database sessions

    Returns:
        Dictionary with list of datasets
    """
    try:
        logger.info("Listing available datasets")

        # Use container to access database if available
        if container is not None:
            # Example of how to use container:
            # db_session = container.get_database_session()
            # datasets = db_session.query(Dataset).all()
            pass

        # Simulate dataset listing
        await asyncio.sleep(0.05)  # Simulate processing time

        datasets = [
            {
                "id": "ds_demo",
                "name": "Demo Dataset",
                "description": "Sample dataset for demonstration",
                "document_count": 5,
                "created_at": "2023-01-01T00:00:00Z",
            },
            {
                "id": "ds_docs",
                "name": "Documentation",
                "description": "Technical documentation dataset",
                "document_count": 12,
                "created_at": "2023-01-02T00:00:00Z",
            },
        ]

        return {
            "content": [{"type": "text", "text": f"Available datasets: {datasets}"}],
            "isError": False,
        }
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return {
            "content": [{"type": "text", "text": f"Failed to list datasets: {str(e)}"}],
            "isError": True,
        }


async def create_chat_session(
    dataset_id: str, title: str = "New Chat Session", container=None
) -> Dict[str, Any]:
    """
    Create a new chat session.

    Args:
        dataset_id: ID of the dataset to chat with
        title: Title for the chat session
        container: The application container with database sessions

    Returns:
        Dictionary with session information
    """
    try:
        logger.info(f"Creating chat session for dataset {dataset_id}")

        # Use container to access database if available
        if container is not None:
            # Example of how to use container:
            # db_session = container.get_database_session()
            # session = ChatSession(dataset_id=dataset_id, title=title)
            # db_session.add(session)
            # db_session.commit()
            pass

        # Simulate session creation
        await asyncio.sleep(0.05)  # Simulate processing time

        session_id = f"session_{hash(dataset_id + title) % 1000000}"

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Created chat session {session_id} for dataset {dataset_id}",
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
