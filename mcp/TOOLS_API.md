# RAPTOR MCP Tools API Documentation

## Overview

This document provides detailed API documentation for all tools exposed by the RAPTOR MCP Service. These tools allow AI assistants to interact with the RAPTOR document processing and retrieval system.

## Tool Categories

The RAPTOR MCP tools are organized into the following categories:

1. **Base Tools**: Core functionality for dataset and session management
2. **Document Tools**: Document ingestion and retrieval operations
3. **RAG Tools**: Retrieval-Augmented Generation tools for working with the RAPTOR tree structure
4. **Resource Handlers**: Functions for accessing RAPTOR resources

## Base Tools

### list_datasets

Lists all available datasets in the RAPTOR service.

**Signature:**

```python
async def list_datasets(container=None) -> Dict[str, Any]
```

**Parameters:**

- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Available datasets: [{dataset_info}, ...]"
        }
    ],
    "isError": bool
}
```

**Example Response:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Available datasets: [{'id': 'ds_demo', 'name': 'Demo Dataset', ...}]"
    }
  ],
  "isError": false
}
```

### create_chat_session

Creates a new chat session for interacting with a specific dataset.

**Signature:**

```python
async def create_chat_session(
    dataset_id: str,
    title: str = "New Chat Session",
    container=None
) -> Dict[str, Any]
```

**Parameters:**

- `dataset_id` (str): ID of the dataset to use for the chat session
- `title` (str, optional): Title for the chat session (default: "New Chat Session")
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Successfully created chat session {session_id} for dataset {dataset_id} with title '{title}'"
        }
    ],
    "isError": bool
}
```

### ingest_document

Ingests a document into the RAPTOR service.

**Signature:**

```python
async def ingest_document(
    dataset_id: str,
    file_content: str,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    container=None
) -> Dict[str, Any]
```

**Parameters:**

- `dataset_id` (str): ID of the dataset to ingest into
- `file_content` (str): Content of the document to ingest
- `source` (str, optional): Source of the document
- `tags` (List[str], optional): Tags to associate with the document
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Successfully ingested document into dataset {dataset_id}. Document ID: {doc_id}, Chunks: {chunks}"
        }
    ],
    "isError": bool
}
```

## Document Tools

### answer_question

Answers a question using RAPTOR's retrieval and LLM capabilities.

**Signature:**

```python
async def answer_question(
    dataset_id: str,
    query: str,
    mode: str = "collapsed",
    top_k: int = 5,
    temperature: float = 0.7,
    container=None
) -> Dict[str, Any]
```

**Parameters:**

- `dataset_id` (str): ID of the dataset to use for answering
- `query` (str): Question to answer
- `mode` (str, optional): Retrieval mode ("collapsed" or "traversal", default: "collapsed")
- `top_k` (int, optional): Number of relevant documents to consider (default: 5)
- `temperature` (float, optional): LLM temperature for answer generation (default: 0.7)
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Answer: {answer_text}\n\nContext: {context}"
        }
    ],
    "isError": bool
}
```

### retrieve_documents

Retrieves relevant documents for a query.

**Signature:**

```python
async def retrieve_documents(
    dataset_id: str,
    query: str,
    mode: str = "collapsed",
    top_k: int = 5,
    expand_k: int = 3
) -> Dict[str, Any]
```

**Parameters:**

- `dataset_id` (str): ID of the dataset to search
- `query` (str): Search query
- `mode` (str, optional): Retrieval mode ("collapsed" or "traversal", default: "collapsed")
- `top_k` (int, optional): Number of relevant documents to consider (default: 5)
- `expand_k` (int, optional): Number of nodes to expand (default: 3)

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Retrieved documents: [{document_info}, ...]"
        }
    ],
    "isError": bool
}
```

## RAG Tools

### rag_retrieve

Retrieves relevant documents/nodes based on a query using RAPTOR's tree-based retrieval.

**Signature:**

```python
async def rag_retrieve(
    dataset_id: str,
    query: str,
    top_k: int = 5,
    levels_cap: Optional[int] = None,
    expand_k: Optional[int] = None,
    reranker: Optional[bool] = None,
    score_threshold: Optional[float] = None,
    container=None
) -> Dict[str, Any]
```

**Parameters:**

- `dataset_id` (str): ID of the dataset to search
- `query` (str): Search query
- `top_k` (int, optional): Number of top results to return (default: 5)
- `levels_cap` (int, optional): Maximum tree levels to traverse
- `expand_k` (int, optional): Number of nodes to expand (for collapsed mode)
- `reranker` (bool, optional): Whether to use a reranker
- `score_threshold` (float, optional): Minimum score threshold for results
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "resource",
            "resource": {
                "uri": "raptor://{dataset_id}/nodes/{node_id}",
                "mimeType": "text/plain",
                "text": "{node_content}",
                "metadata": {
                    "score": float,
                    "chunk_id": str,
                    "doc_id": str
                }
            }
        },
        ...
    ],
    "isError": bool
}
```

### rag_node_get

Retrieves metadata and content of a specific RAPTOR tree node.

**Signature:**

```python
async def rag_node_get(node_id: str, container) -> Dict[str, Any]
```

**Parameters:**

- `node_id` (str): ID of the node to retrieve
- `container`: Application container with database sessions (required)

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Node metadata: {metadata}"
        }
    ],
    "isError": bool
}
```

### rag_node_children

Lists child nodes of a given RAPTOR tree node.

**Signature:**

```python
async def rag_node_children(node_id: str, container=None) -> Dict[str, Any]
```

**Parameters:**

- `node_id` (str): ID of the parent node
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Child nodes: [{child_info}, ...]"
        }
    ],
    "isError": bool
}
```

### rag_node_navigation

Navigates to parent or sibling nodes in the RAPTOR tree.

**Signature:**

```python
async def rag_node_navigation(
    node_id: str,
    direction: str,
    container=None
) -> Dict[str, Any]
```

**Parameters:**

- `node_id` (str): ID of the node to navigate from
- `direction` (str): Direction to navigate ("parent" or "siblings")
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "{direction.capitalize()}: {navigation_result}"
        }
    ],
    "isError": bool
}
```

### rag_path_to_root

Gets the path from a node to the root of the RAPTOR tree.

**Signature:**

```python
async def rag_path_to_root(node_id: str, container=None) -> Dict[str, Any]
```

**Parameters:**

- `node_id` (str): ID of the starting node
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Path to root: {path_description}"
        }
    ],
    "isError": bool
}
```

### rag_summarize

Generates a summary of selected RAPTOR tree nodes.

**Signature:**

```python
async def rag_summarize(node_ids: List[str], container=None) -> Dict[str, Any]
```

**Parameters:**

- `node_ids` (List[str]): List of node IDs to summarize
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "{summary_text}"
        }
    ],
    "isError": bool
}
```

## Resource Handlers

### read_resource

Reads a RAPTOR resource with real database connectivity.

**Signature:**

```python
async def read_resource(uri: str, container=None) -> Dict[str, Any]
```

**Parameters:**

- `uri` (str): URI of the resource to read (format: `raptor://{dataset_id}/nodes/{node_id}`)
- `container` (optional): Application container with database sessions

**Returns:**

```python
{
    "contents": [
        {
            "uri": str,
            "mimeType": "text/plain",
            "text": "{resource_content}"
        }
    ]
}
```

## Error Handling

All tools follow a consistent error handling pattern:

**Success Response:**

```python
{
    "content": [...],  # Tool-specific content
    "isError": false
}
```

**Error Response:**

```python
{
    "content": [
        {
            "type": "text",
            "text": "Error description"
        }
    ],
    "isError": true
}
```

## Usage Examples

### Using Tools with an AI Assistant

When an AI assistant connects through MCP, it can call these tools:

```json
{
  "method": "tools/call",
  "params": {
    "name": "rag_retrieve",
    "arguments": {
      "dataset_id": "my_dataset",
      "query": "How do I configure the MCP service?",
      "top_k": 3
    }
  }
}
```

### Direct Tool Usage in Application Code

```python
from mcp.tools import rag_retrieve

# Call the tool directly
result = await rag_retrieve(
    dataset_id="my_dataset",
    query="How do I configure the MCP service?",
    top_k=3
)

if not result["isError"]:
    # Process the retrieved documents
    documents = result["content"]
    # ...
```

## Tool Dependencies

Some tools require database connectivity through the container:

- `rag_node_get` (requires container)
- `rag_retrieve` (requires container)
- `answer_question` (when using real database)
- `list_datasets` (when using real database)
- `create_chat_session` (when using real database)
- `ingest_document` (when using real database)
- `rag_node_children` (when using real database)
- `rag_node_navigation` (when using real database)
- `rag_path_to_root` (when using real database)
- `rag_summarize` (when using real database)
- `read_resource` (when using real database)

Tools without container requirements will return simulated data for testing purposes.
