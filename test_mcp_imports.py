#!/usr/bin/env python3
"""
Test script to verify MCP imports work correctly
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing MCP imports...")

try:
    # Test importing the installed MCP package
    from mcp.server.fastmcp import FastMCP

    print("✓ Successfully imported FastMCP from installed mcp package")
except ImportError as e:
    print(f"✗ Failed to import FastMCP: {e}")

try:
    # Test importing your project's MCP module
    from mcp_local.raptor_mcp_server import create_standalone_mcp_service

    print("✓ Successfully imported create_standalone_mcp_service from project mcp module")
except ImportError as e:
    print(f"✗ Failed to import create_standalone_mcp_service: {e}")

try:
    from app.config import settings

    print("✓ Successfully imported settings from app.config")
    print(f"  PG_ASYNC_DSN: {settings.pg_async_dsn}")
except ImportError as e:
    print(f"✗ Failed to import settings: {e}")
except Exception as e:
    print(f"✗ Error accessing settings: {e}")

print("Import test completed.")
