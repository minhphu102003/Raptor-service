# MCP Service Configuration

## Overview

The RAPTOR MCP Service can be configured through the [MCPConfig](file:///d:/AI/Raptor-service/mcp/config.py#L7-L25) class or environment variables. This document details all available configuration options.

## Configuration Class

The main configuration class is [MCPConfig](file:///d:/AI/Raptor-service/mcp/config.py#L7-L25) in [config.py](file:///d:/AI/Raptor-service/mcp/config.py):

```python
class MCPConfig(BaseModel):
    """Configuration for Model Control Protocol endpoints"""

    # MCP endpoint configurations
    endpoints: Dict[str, Dict[str, str]] = {
        "default": {
            "base_url": "http://localhost:8001",
            "api_key": "",  # Optional API key
        }
    }

    # Default summarization settings for MCP models
    summarization_max_tokens: int = 1000
    summarization_temperature: float = 0.3

    # Throttling settings
    rpm_limit: int = 60  # Requests per minute
    max_concurrent: int = 5
```

## Configuration Options

### Endpoint Configuration

- **endpoints**: A dictionary of MCP endpoint configurations
  - **default**: The default endpoint configuration
    - **base_url**: The base URL for the MCP service (default: "http://localhost:8001")
    - **api_key**: Optional API key for authentication (default: "")

### Summarization Settings

- **summarization_max_tokens**: Maximum number of tokens for summarization responses (default: 1000)
- **summarization_temperature**: Temperature setting for LLM summarization (default: 0.3)

### Throttling Settings

- **rpm_limit**: Requests per minute limit to prevent overloading (default: 60)
- **max_concurrent**: Maximum number of concurrent requests (default: 5)

## Environment Variables

All configuration options can be set using environment variables with the `MCP_` prefix:

```bash
# Endpoint configuration
MCP_ENDPOINTS_DEFAULT_BASE_URL=http://localhost:8001
MCP_ENDPOINTS_DEFAULT_API_KEY=your_api_key

# Summarization settings
MCP_SUMMARIZATION_MAX_TOKENS=1000
MCP_SUMMARIZATION_TEMPERATURE=0.3

# Throttling settings
MCP_RPM_LIMIT=60
MCP_MAX_CONCURRENT=5
```

## Usage Examples

### Python Configuration

```python
from mcp.config import MCPConfig

# Create custom configuration
config = MCPConfig(
    endpoints={
        "default": {
            "base_url": "https://your-mcp-service.com",
            "api_key": "your_api_key_here"
        }
    },
    summarization_max_tokens=1500,
    rpm_limit=100
)

# Use the configuration
# (Note: The current implementation uses a global config instance)
```

### Environment Variable Configuration

```bash
# Set environment variables
export MCP_ENDPOINTS_DEFAULT_BASE_URL=https://your-mcp-service.com
export MCP_ENDPOINTS_DEFAULT_API_KEY=your_api_key_here
export MCP_SUMMARIZATION_MAX_TOKENS=1500
export MCP_RPM_LIMIT=100

# Run your application
python your_app.py
```

## Best Practices

1. **Security**: Never hardcode API keys in your source code. Use environment variables or secure configuration management systems.

2. **Rate Limiting**: Adjust the `rpm_limit` and `max_concurrent` settings based on your infrastructure capacity and the LLM provider's rate limits.

3. **Summarization Quality**: Tune the `summarization_temperature` and `summarization_max_tokens` based on your use case:

   - Lower temperature (0.1-0.3) for more deterministic summaries
   - Higher temperature (0.7-1.0) for more creative summaries
   - Adjust max_tokens based on desired summary length

4. **Endpoint Configuration**: When deploying to production, ensure your `base_url` points to the correct public endpoint.

## Troubleshooting

### Common Issues

1. **Connection Refused**: Verify that the `base_url` is correctly configured and the service is running.

2. **Authentication Errors**: Ensure the `api_key` is correctly set if authentication is required.

3. **Rate Limiting**: If you're hitting rate limits, consider adjusting the `rpm_limit` and `max_concurrent` settings.

### Configuration Validation

The configuration is validated using Pydantic, so any invalid values will raise validation errors at startup.
