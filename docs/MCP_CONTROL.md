# MCP Server Control

This document describes how to control the MCP server startup in the RAPTOR service.

## Overview

The RAPTOR service now supports controlling whether the MCP server starts through configuration and command-line flags.

## Configuration Options

### Environment Variable

You can control the MCP server through the `APP_MCP_ENABLED` environment variable:

```bash
# Disable MCP server
APP_MCP_ENABLED=false uv run fastapi run app/main.py

# Enable MCP server (default)
APP_MCP_ENABLED=true uv run fastapi run app/main.py
```

### Command Line Flag

You can also disable the MCP server using a command-line flag:

```bash
# Disable MCP server
uv run fastapi run app/main.py --disable-mcp

# Enable MCP server (default behavior)
uv run fastapi run app/main.py
```

## Configuration File

The MCP server can also be controlled through the application configuration in `app/config.py`. By default, the MCP server is enabled (`mcp_enabled: bool = True`).

## Precedence

The precedence for MCP server control is as follows:

1. Command-line flag (`--disable-mcp`) - highest precedence
2. Environment variable (`APP_MCP_ENABLED`) - medium precedence
3. Configuration file default (`mcp_enabled = True`) - lowest precedence

## Usage Examples

### Development

```bash
# Run with MCP enabled (default)
uv run fastapi dev app/main.py

# Run with MCP disabled
uv run fastapi dev app/main.py --disable-mcp
```

### Production

```bash
# Run with MCP enabled (default)
uv run fastapi run app/main.py

# Run with MCP disabled
uv run fastapi run app/main.py --disable-mcp
```

### With Docker

```bash
# Run with MCP enabled (default)
docker run -p 8000:8000 raptor-service

# Run with MCP disabled
docker run -p 8000:8000 -e APP_MCP_ENABLED=false raptor-service
```

## Benefits

1. **Flexibility**: You can choose whether to run the MCP server based on your needs
2. **Resource Management**: Disable MCP when not needed to save resources
3. **Environment-Specific Configuration**: Enable MCP in development but disable in production if needed
4. **Troubleshooting**: Easily disable MCP to isolate issues
