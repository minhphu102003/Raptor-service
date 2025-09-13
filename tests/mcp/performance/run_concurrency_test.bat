@echo off
echo MCP Concurrency Test Runner
echo =========================

echo Starting MCP server in HTTP mode on port 3333...
start "MCP Server" /MIN python run_mcp_server.py --mode http --host 127.0.0.1 --port 3333

echo Waiting 5 seconds for server to start...
timeout /t 5 /nobreak >nul

echo Running concurrency test...
python test_mcp_concurrency.py

echo Test completed.
pause
