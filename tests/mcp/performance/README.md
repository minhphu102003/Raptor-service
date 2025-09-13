# MCP Server Performance and Concurrency Testing

This directory contains scripts and tools for testing the performance and concurrency handling of the MCP server.

## Test Scripts Overview

Three test scripts are provided:

1. `test_mcp_concurrency.py` - Tests general MCP protocol concurrency with list_tools calls
2. `test_rag_retrieve_concurrency.py` - Tests concurrency with rag_retrieve tool calls
3. `run_concurrency_test.bat` - Windows batch script to run the tests

## Prerequisites

1. Make sure your MCP server is running
2. Install required Python packages:
   ```bash
   pip install aiohttp
   ```

## Running the Tests

### Option 1: Using the Batch Script (Windows)

1. Run the batch script which will automatically start the server:
   ```bash
   run_concurrency_test.bat
   ```

### Option 2: Manual Testing

1. Start your MCP server in HTTP mode:

   ```bash
   python run_mcp_server.py --mode http --host 127.0.0.1 --port 3333
   ```

2. In another terminal, run one of the test scripts:

   ```bash
   # Test general MCP concurrency
   python test_mcp_concurrency.py

   # Test RAG retrieve tool concurrency
   python test_rag_retrieve_concurrency.py
   ```

## Test Configuration

You can modify the test parameters in each script:

- `num_requests`: Total number of requests to send
- `max_concurrent`: Maximum number of concurrent requests
- `dataset_id`: For RAG retrieve tests, specify a valid dataset ID

## Expected Results

If your server properly handles concurrent requests, you should see:

- All requests completing successfully
- Reasonable response times
- No server crashes or hangs

## Interpreting Results

The tests will show:

- Success rate (successful requests / total requests)
- Response time statistics (average, min, max)
- Any errors encountered

If you see failures, check:

1. Server logs for error messages
2. Database connection limits
3. System resource usage (CPU, memory)
4. Network connectivity issues

## Troubleshooting

### Server Not Responding

- Ensure the MCP server is running on the correct host and port
- Check firewall settings
- Verify the server is not blocked by antivirus software

### Connection Errors

- Check that the server URL in the test script matches your server configuration
- Ensure the server supports the HTTP transport mode

### Performance Issues

- Monitor system resources during testing
- Adjust the concurrency level to match your system capabilities
- Check database connection pooling settings
