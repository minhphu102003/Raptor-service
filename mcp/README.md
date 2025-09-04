# RAPTOR MCP (Model Context Protocol) Service

## Overview

The RAPTOR MCP Service provides integration with AI assistants through the Model Context Protocol (MCP), an open standard that enables AI models to access and interact with application data and functionality in a structured way. This service exposes the RAPTOR document processing and retrieval capabilities as MCP tools and resources that can be consumed by AI assistants.

## What is Model Context Protocol (MCP)?

Model Context Protocol (MCP) is an open standard that standardizes how applications provide context to large language models (LLMs). Think of MCP like a USB-C port for AI - it provides a universal interface for AI assistants to connect to various tools, data sources, and services.

Key benefits of MCP:

- **Standardization**: Provides a consistent way for AI models to access application capabilities
- **Interoperability**: Works across different AI assistants and platforms
- **Security**: Offers controlled access to application data and functionality
- **Extensibility**: Allows applications to expose their features as standardized tools

## Features

The RAPTOR MCP Service exposes the following capabilities:

### Tools

1. **Document Management Tools**

   - `list_datasets`: List all available datasets
   - `create_chat_session`: Create a new chat session for a dataset
   - `ingest_document`: Ingest a document into a dataset

2. **RAG (Retrieval-Augmented Generation) Tools**

   - `rag_retrieve`: Retrieve relevant documents/nodes based on a query
   - `rag_node_get`: Get metadata and content of a specific node
   - `rag_node_children`: List child nodes of a given node
   - `rag_node_navigation`: Navigate to parent or sibling nodes
   - `rag_path_to_root`: Get the path from a node to the root of the tree
   - `rag_summarize`: Generate a summary of selected nodes

3. **Question Answering Tools**
   - `answer_question`: Answer a question using RAPTOR's retrieval and LLM capabilities
   - `retrieve_documents`: Retrieve relevant documents for a query

### Resources

- **Node Content Resources**: Access to individual RAPTOR tree nodes via `raptor://{dataset_id}/nodes/{node_id}` URIs

## Installation

To use the MCP service, you need to install the MCP package:

```bash
pip install mcp[cli]
```

## Configuration

The MCP service can be configured through the [MCPConfig](file:///d:/AI/Raptor-service/mcp/config.py#L7-L25) class in [config.py](file:///d:/AI/Raptor-service/mcp/config.py):

```python
# Default configuration
endpoints = {
    "default": {
        "base_url": "http://localhost:8001",
        "api_key": "",  # Optional API key
    }
}

# Summarization settings
summarization_max_tokens = 1000
summarization_temperature = 0.3

# Throttling settings
rpm_limit = 60  # Requests per minute
max_concurrent = 5
```

Configuration can also be set through environment variables with the `MCP_` prefix.

## Usage

### Integration with FastAPI Application

The MCP service is designed to integrate with your FastAPI application:

```python
from mcp import RaptorMCPService

# In your FastAPI app setup
app = FastAPI()
app.state.container = your_container  # Your application container with database sessions

# Create MCP service with your container
mcp_service = RaptorMCPService(container=app.state.container)

# Get the MCP server instance
mcp_server = mcp_service.get_mcp_server()

# Mount to your FastAPI app (if using SSE)
from mcp.sse_endpoint import mount_sse_endpoints
mount_sse_endpoints(app)
```

### Standalone Usage

For standalone usage, you can create an MCP service with database connectivity:

```python
from mcp import create_standalone_mcp_service

# Create service with database connection strings
mcp_service = create_standalone_mcp_service(
    db_dsn="postgresql://user:password@localhost:5432/db",
    vector_dsn="postgresql://user:password@localhost:5432/vector_db"
)
```

## Tool Details

### Document Management Tools

#### `list_datasets`

Lists all available datasets in the RAPTOR service.

#### `create_chat_session`

Creates a new chat session for interacting with a specific dataset.

Parameters:

- `dataset_id` (str): ID of the dataset to use for the chat session
- `title` (str, optional): Title for the chat session (default: "New Chat Session")

#### `ingest_document`

Ingests a document into the RAPTOR service.

Parameters:

- `dataset_id` (str): ID of the dataset to ingest into
- `file_content` (str): Content of the document to ingest
- `source` (str, optional): Source of the document
- `tags` (List[str], optional): Tags to associate with the document

### RAG Tools

#### `rag_retrieve`

Retrieves relevant documents/nodes based on a query using RAPTOR's tree-based retrieval.

Parameters:

- `dataset_id` (str): ID of the dataset to search
- `query` (str): Search query
- `top_k` (int, optional): Number of top results to return (default: 5)
- `levels_cap` (int, optional): Maximum tree levels to traverse
- `expand_k` (int, optional): Number of nodes to expand (for collapsed mode)
- `reranker` (bool, optional): Whether to use a reranker
- `score_threshold` (float, optional): Minimum score threshold for results

#### `rag_node_get`

Retrieves metadata and content of a specific RAPTOR tree node.

Parameters:

- `node_id` (str): ID of the node to retrieve

#### `rag_node_children`

Lists child nodes of a given RAPTOR tree node.

Parameters:

- `node_id` (str): ID of the parent node

#### `rag_node_navigation`

Navigates to parent or sibling nodes in the RAPTOR tree.

Parameters:

- `node_id` (str): ID of the node to navigate from
- `direction` (str): Direction to navigate ("parent" or "siblings")

#### `rag_path_to_root`

Gets the path from a node to the root of the RAPTOR tree.

Parameters:

- `node_id` (str): ID of the starting node

#### `rag_summarize`

Generates a summary of selected RAPTOR tree nodes.

Parameters:

- `node_ids` (List[str]): List of node IDs to summarize

### Question Answering Tools

#### `answer_question`

Answers a question using RAPTOR's retrieval and LLM capabilities.

Parameters:

- `dataset_id` (str): ID of the dataset to use for answering
- `query` (str): Question to answer
- `mode` (str, optional): Retrieval mode ("collapsed" or "traversal", default: "collapsed")
- `top_k` (int, optional): Number of relevant documents to consider (default: 5)
- `temperature` (float, optional): LLM temperature for answer generation (default: 0.7)

#### `retrieve_documents`

Retrieves relevant documents for a query.

Parameters:

- `dataset_id` (str): ID of the dataset to search
- `query` (str): Search query
- `mode` (str, optional): Retrieval mode ("collapsed" or "traversal", default: "collapsed")
- `top_k` (int, optional): Number of relevant documents to consider (default: 5)
- `expand_k` (int, optional): Number of nodes to expand (default: 3)

## Resource Access

RAPTOR nodes can be accessed as resources using the URI format:

```
raptor://{dataset_id}/nodes/{node_id}
```

For example:

```
raptor://my_dataset/nodes/node_12345
```

## Architecture

The MCP service follows a modular architecture:

```
MCP Service
├── Configuration ([config.py](file:///d:/AI/Raptor-service/mcp/config.py))
├── Server Implementation ([raptor_mcp_server.py](file:///d:/AI/Raptor-service/mcp/raptor_mcp_server.py))
├── Tools
│   ├── Base Tools ([base_tools.py](file:///d:/AI/Raptor-service/mcp/tools/base_tools.py))
│   ├── Document Tools ([document_tools.py](file:///d:/AI/Raptor-service/mcp/tools/document_tools.py))
│   ├── RAG Navigation ([rag_navigation.py](file:///d:/AI/Raptor-service/mcp/tools/rag_navigation.py))
│   ├── RAG Node ([rag_node.py](file:///d:/AI/Raptor-service/mcp/tools/rag_node.py))
│   ├── RAG Retrieve ([rag_retrieve.py](file:///d:/AI/Raptor-service/mcp/tools/rag_retrieve.py))
│   ├── RAG Summarize ([rag_summarize.py](file:///d:/AI/Raptor-service/mcp/tools/rag_summarize.py))
│   └── Resources ([resources.py](file:///d:/AI/Raptor-service/mcp/tools/resources.py))
└── SSE Endpoint ([sse_endpoint.py](file:///d:/AI/Raptor-service/mcp/sse_endpoint.py))
```

## Development

### Adding New Tools

To add a new tool to the MCP service:

1. Create a new tool function in the appropriate file in the [tools](file:///d:/AI/Raptor-service/mcp/tools/) directory
2. Add the function to the `__all__` list in [tools/**init**.py](file:///d:/AI/Raptor-service/mcp/tools/__init__.py)
3. Register the tool in the [\_register_tools](file:///d:/AI/Raptor-service/mcp/raptor_mcp_server.py#L78-L186) method in [raptor_mcp_server.py](file:///d:/AI/Raptor-service/mcp/raptor_mcp_server.py)

### Adding New Resources

To add a new resource type:

1. Create a resource handler function in [tools/resources.py](file:///d:/AI/Raptor-service/mcp/tools/resources.py)
2. Register the resource in the [\_register_resources](file:///d:/AI/Raptor-service/mcp/raptor_mcp_server.py#L188-L201) method in [raptor_mcp_server.py](file:///d:/AI/Raptor-service/mcp/raptor_mcp_server.py)

## Error Handling

All tools return a consistent response format:

```python
{
    "content": [...],  # Content blocks with the response
    "isError": bool    # Whether an error occurred
}
```

When `isError` is `True`, the content will contain error information.

## Security Considerations

- The service uses container-based dependency injection to ensure proper access controls
- Database access is managed through Unit of Work patterns
- All database operations are performed within transactions
- API keys and sensitive configuration can be provided through environment variables

## Running the Service

To run the MCP service standalone:

```bash
python -m mcp.raptor_mcp_server serve
```

Or from the module directly:

```bash
python raptor_mcp_server.py serve
```

## Integration Examples

### With Claude Desktop

To integrate with Claude Desktop, add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "raptor": {
      "command": "python",
      "args": ["-m", "mcp.raptor_mcp_server"],
      "env": {
        "MCP_BASE_URL": "http://localhost:8001"
      }
    }
  }
}
```

### With Other MCP-Capable Applications

Any application that supports MCP can connect to the RAPTOR service by configuring the appropriate connection parameters.

## Troubleshooting

Common issues and solutions:

1. **MCP not available error**: Ensure you've installed the MCP package with `pip install mcp[cli]`
2. **Container required error**: Make sure you're passing a valid container with database connectivity
3. **Database connection issues**: Verify your database connection strings in the container configuration

## Contributing

Contributions to the RAPTOR MCP service are welcome. Please follow the standard contribution guidelines for the project.

## License

This project is licensed under the terms specified in the main RAPTOR service license.
