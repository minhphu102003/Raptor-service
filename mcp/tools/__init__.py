"""MCP Tools Package for RAPTOR Service

This package contains all the individual tools that are exposed via the MCP server.
"""

# Import all tool functions for easier access
from .base_tools import create_chat_session, ingest_document, list_datasets
from .document_tools import answer_question, retrieve_documents
from .rag_tools import (
    rag_node_children,
    rag_node_get,
    rag_node_navigation,
    rag_path_to_root,
    rag_retrieve,
    rag_summarize,
)
from .resources import read_resource

__all__ = [
    # Base tools
    "list_datasets",
    "create_chat_session",
    "ingest_document",
    # RAG tools
    "rag_retrieve",
    "rag_node_get",
    "rag_node_children",
    "rag_node_navigation",
    "rag_path_to_root",
    "rag_summarize",
    # Document tools
    "retrieve_documents",
    "answer_question",
    # Resources
    "read_resource",
]
