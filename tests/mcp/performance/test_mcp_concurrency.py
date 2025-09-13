import asyncio
import json
import logging
import time
from typing import Dict, List

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MCPConcurrencyTester:
    def __init__(self, base_url: str = "http://127.0.0.1:3333"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_initialize_request(self, request_id: int) -> Dict:
        """Send an initialize request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-01-01",
                "capabilities": {},
                "clientInfo": {"name": "concurrency-tester", "version": "1.0.0"},
            },
        }

        try:
            async with self.session.post(f"{self.base_url}/mcp/messages", json=payload) as response:
                response_data = await response.json()
                return {
                    "request_id": request_id,
                    "status": response.status,
                    "success": response.status == 200,
                    "response": response_data,
                }
        except Exception as e:
            logger.error(f"Initialize request {request_id} failed: {str(e)}")
            return {"request_id": request_id, "status": None, "success": False, "error": str(e)}

    async def send_list_tools_request(self, request_id: int) -> Dict:
        """Send a list_tools request to the MCP server"""
        payload = {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": {}}

        try:
            async with self.session.post(f"{self.base_url}/mcp/messages", json=payload) as response:
                # Handle case where response might not be JSON
                try:
                    response_data = await response.json()
                except:
                    # If JSON parsing fails, get text content
                    text_content = await response.text()
                    response_data = {"error": "Non-JSON response", "content": text_content}

                return {
                    "request_id": request_id,
                    "status": response.status,
                    "success": response.status == 200,
                    "response": response_data,
                }
        except Exception as e:
            logger.error(f"List tools request {request_id} failed: {str(e)}")
            return {"request_id": request_id, "status": None, "success": False, "error": str(e)}

    async def send_tool_call_request(
        self, request_id: int, tool_name: str, arguments: Dict
    ) -> Dict:
        """Send a tool call request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            start_time = time.time()
            async with self.session.post(f"{self.base_url}/mcp/messages", json=payload) as response:
                response_time = time.time() - start_time
                # Handle case where response might not be JSON
                try:
                    response_data = await response.json()
                except:
                    # If JSON parsing fails, get text content
                    text_content = await response.text()
                    response_data = {"error": "Non-JSON response", "content": text_content}

                result = {
                    "request_id": request_id,
                    "status": response.status,
                    "response_time": response_time,
                    "success": response.status == 200,
                    "response": response_data,
                }

                if response.status == 200:
                    logger.info(f"Tool call {request_id} succeeded in {response_time:.3f}s")
                else:
                    logger.warning(f"Tool call {request_id} failed with status {response.status}")

                return result
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Tool call {request_id} failed: {str(e)}")
            return {
                "request_id": request_id,
                "status": None,
                "response_time": response_time,
                "success": False,
                "error": str(e),
            }

    async def run_concurrent_tool_calls(
        self, num_requests: int = 10, max_concurrent: int = 5
    ) -> List[Dict]:
        """Run multiple concurrent tool call requests"""
        logger.info(
            f"Starting concurrent tool call test: {num_requests} requests, max {max_concurrent} concurrent"
        )

        start_time = time.time()

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_tool_call(request_id):
            async with semaphore:
                # Use a simple test argument that won't require actual dataset
                return await self.send_tool_call_request(
                    request_id,
                    "rag_retrieve",
                    {"dataset_id": "test_dataset", "query": f"Test query {request_id}"},
                )

        # Create tasks for all requests
        tasks = [limited_tool_call(i) for i in range(num_requests)]

        # Run all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Process results
        successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed_requests = num_requests - successful_requests

        # Calculate statistics
        response_times = [
            r["response_time"] for r in results if isinstance(r, dict) and "response_time" in r
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0

        logger.info(f"Test completed in {total_time:.3f}s")
        logger.info(f"Successful requests: {successful_requests}/{num_requests}")
        logger.info(f"Failed requests: {failed_requests}")
        logger.info(f"Average response time: {avg_response_time:.3f}s")
        logger.info(f"Min response time: {min_response_time:.3f}s")
        logger.info(f"Max response time: {max_response_time:.3f}s")

        return results


async def main():
    """Main function to run the concurrency test"""
    logger.info("Starting MCP Concurrency Test")

    # Connect to 127.0.0.1 for local testing
    async with MCPConcurrencyTester("http://127.0.0.1:3333") as tester:
        # First, test initialization
        logger.info("Testing server initialization...")
        init_result = await tester.send_initialize_request(0)
        logger.info(f"Initialization result: {init_result}")

        # Then test a simple request to make sure server is responsive
        logger.info("Testing server connectivity...")
        list_result = await tester.send_list_tools_request(1)
        logger.info(f"List tools result: {list_result}")

        if not list_result["success"]:
            logger.error(
                "Server is not responding correctly. Please make sure the MCP server is running."
            )
            # Print response content for debugging
            if "response" in list_result:
                logger.error(f"Response content: {list_result['response']}")
            return

        # Run concurrency test
        # You can adjust these parameters:
        # - num_requests: Total number of requests to send
        # - max_concurrent: Maximum number of concurrent requests
        logger.info("Running concurrent requests test...")
        results = await tester.run_concurrent_tool_calls(num_requests=15, max_concurrent=5)

        # Print summary
        print("\n=== MCP CONCURRENCY TEST RESULTS ===")
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        print(f"Successful requests: {successful}/{len(results)}")

        if successful > 0:
            response_times = [
                r["response_time"] for r in results if isinstance(r, dict) and r.get("success")
            ]
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                print(f"Average response time: {avg_time:.3f}s")

        # Check for any errors
        errors = [
            r
            for r in results
            if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success"))
        ]
        if errors:
            print(f"\nErrors found: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
        else:
            print("\nNo errors found. All requests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
