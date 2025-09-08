# RAPTOR MCP Server Integration with Qoder IDE

## Overview

This guide provides specific instructions for running the RAPTOR MCP (Model Context Protocol) server and integrating it with Qoder IDE. The RAPTOR MCP server exposes document processing and retrieval capabilities through the Model Context Protocol, enabling Qoder to access your knowledge base for AI-assisted development.

## Prerequisites

1. RAPTOR service properly installed and configured
2. Python 3.11+ environment
3. Qoder IDE installed
4. PostgreSQL database with pgvector extension

## Running the RAPTOR MCP Server

### HTTP Mode (Recommended for Qoder)

To run the MCP server in HTTP mode for integration with Qoder:

```bash
# Navigate to your RAPTOR service directory
cd d:\AI\Raptor-service

# Run the MCP server in HTTP mode
python run_mcp_server.py --mode http --host 127.0.0.1 --port 3333
```

The server will start and be accessible at `http://127.0.0.1:3333/mcp`.

### Stdio Mode (Alternative)

For direct stdio communication:

```bash
python run_mcp_server.py --mode stdio
```

## Integrating with Qoder IDE

### 1. Configure Qoder MCP Settings

In Qoder, create or update your `mcp.json` configuration file with the following content:

```json
{
  "mcpServers": {
    "raptor": {
      "url": "http://127.0.0.1:3333/mcp"
    }
  }
}
```

### 2. Verify Connection

1. Start the RAPTOR MCP server using the HTTP mode command above
2. Open Qoder IDE
3. Check the MCP connection status in Qoder
4. You should see the "raptor" server connected and available

## Available RAPTOR Tools in Qoder

Once integrated, Qoder can access the following RAPTOR tools:

### Document Management
- `list_datasets`: List all available datasets
- `create_chat_session`: Create a new chat session for a dataset
- `ingest_document`: Ingest a document into a dataset

### RAG (Retrieval-Augmented Generation) Tools
- `rag_retrieve`: Retrieve relevant documents/nodes based on a query
- `rag_node_get`: Get metadata and content of a specific node
- `rag_node_children`: List child nodes of a given node
- `rag_node_navigation`: Navigate to parent or sibling nodes
- `rag_path_to_root`: Get the path from a node to the root of the tree
- `rag_summarize`: Generate a summary of selected nodes

### Question Answering
- `answer_question`: Answer questions using RAPTOR's retrieval and LLM capabilities

## Usage Examples in Qoder

### In Qoder Chat
Once connected, you can use these tools directly in Qoder's chat interface:

```
User: List all available datasets in my RAPTOR service
Qoder: [Automatically calls list_datasets tool]

User: Retrieve information about FastAPI integration from my documentation
Qoder: [Automatically calls rag_retrieve with appropriate parameters]
```

### Context-Aware Code Assistance
Qoder can use RAPTOR tools to provide context-aware code suggestions based on your document knowledge base.

## Troubleshooting Qoder Integration

### Common Issues

1. **Connection Refused**
   - Ensure the RAPTOR MCP server is running before starting Qoder
   - Check that port 3333 is not blocked by firewall
   - Verify the host (127.0.0.1) is correct

2. **Tools Not Appearing in Qoder**
   - Confirm all tools are properly registered in `mcp_local/raptor_mcp_server.py`
   - Check Qoder's MCP connection status
   - Restart both the MCP server and Qoder if needed

3. **Database Connection Issues**
   - Verify your database connection strings in the `.env` file
   - Ensure PostgreSQL with pgvector is running and accessible

### Logs and Debugging

Check the RAPTOR MCP server logs for any error messages:
- Tool registration confirmation
- Database connection status
- Request handling information

In Qoder, check the MCP panel for connection status and tool availability.

## Configuration Options

### Environment Variables

Configure the MCP service through environment variables:

```bash
# Database connections (required)
PG_ASYNC_DSN=postgresql://user:password@localhost:5432/db
VECTOR_DSN=postgresql://user:password@localhost:5432/vector_db

# Optional MCP settings
MCP_SUMMARIZATION_MAX_TOKENS=1000
MCP_RPM_LIMIT=60
```

## Windows Compatibility

The MCP server automatically configures the event loop policy for Windows compatibility:

```python
if sys.platform == "win32":
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
```

This ensures proper operation with async database drivers on Windows.

## Security Considerations

When using the RAPTOR MCP server with Qoder:

- Database credentials should be stored securely in environment variables
- The server should only be accessible from localhost (127.0.0.1) in development
- For production deployments, consider adding authentication and encryption

## Best Practices for Qoder Integration

1. **Start the MCP Server First**: Always start the RAPTOR MCP server before launching Qoder
2. **Use Descriptive Dataset Names**: Organize your documents in clearly named datasets for easier retrieval
3. **Regular Ingestion**: Keep your knowledge base updated by regularly ingesting new documents
4. **Monitor Performance**: Watch for slow responses which might indicate database or network issues

## Advanced Qoder Integration

### Custom Tool Usage

You can directly invoke RAPTOR tools in Qoder chat by specifying the tool name:

```
User: /tool rag_retrieve dataset_id="my_docs" query="How to implement authentication?"
```

### Context Preservation

Qoder maintains context between tool calls, allowing for complex workflows:
1. First, list datasets to identify the correct one
2. Then retrieve relevant information from that dataset
3. Finally, ask specific questions about the retrieved content

## Support and Contributing

For issues with the RAPTOR MCP integration in Qoder:
1. Check that both services are running on compatible versions
2. Verify all environment variables are correctly set
3. Review the logs for error messages
4. Ensure network connectivity between Qoder and the MCP server

For enhancements or bug fixes, please submit issues to the RAPTOR service repository.
