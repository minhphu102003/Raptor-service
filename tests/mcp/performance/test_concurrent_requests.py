import asyncio
import json
import logging
import time
from typing import Dict, List

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPConcurrencyTester:
    def __init__(self, base_url: str = "http://127.0.0.1:3333"):
        self.base_url = base_url
        self.session = None
        self.results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_tool_request(self, request_id: int) -> Dict:
        """Send a single tool request to the MCP server"""
        start_time = time.time()

        # Example request body for rag_retrieve tool
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": "rag_retrieve",
                "arguments": {
                    "dataset_id": "test_dataset",
                    "query": f"Test query {request_id}",
                    "top_k": 5,
                },
            },
        }

        try:
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

                logger.info(
                    f"Request {request_id}: Status {response.status}, Time: {response_time:.3f}s"
                )
                return result

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Request {request_id} failed: {str(e)}")
            return {
                "request_id": request_id,
                "status": None,
                "response_time": response_time,
                "success": False,
                "error": str(e),
            }

    async def run_concurrent_requests(
        self, num_requests: int = 10, max_concurrent: int = 5
    ) -> List[Dict]:
        """Run multiple concurrent requests to test server concurrency"""
        logger.info(
            f"Starting concurrent request test: {num_requests} requests, max {max_concurrent} concurrent"
        )

        start_time = time.time()

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_request(request_id):
            async with semaphore:
                return await self.send_tool_request(request_id)

        # Create tasks for all requests
        tasks = [limited_request(i) for i in range(num_requests)]

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

        self.results = results
        return results


async def main():
    """Main function to run the concurrency test"""
    # Initialize tester - connect to 127.0.0.1 for local testing
    async with MCPConcurrencyTester("http://127.0.0.1:3333") as tester:
        # First, test initialization
        logger.info("Testing server initialization...")
        init_payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-01-01",
                "capabilities": {},
                "clientInfo": {"name": "concurrency-tester", "version": "1.0.0"},
            },
        }

        try:
            async with tester.session.post(
                f"{tester.base_url}/mcp/messages", json=init_payload
            ) as response:
                init_result = await response.json()
                logger.info(f"Initialization result: {init_result}")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return

        # Run concurrency test
        # You can adjust these parameters:
        # - num_requests: Total number of requests to send
        # - max_concurrent: Maximum number of concurrent requests
        results = await tester.run_concurrent_requests(num_requests=20, max_concurrent=10)

        # Print summary
        print("\n=== CONCURRENCY TEST RESULTS ===")
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        print(f"Successful requests: {successful}/{len(results)}")

        if successful > 0:
            response_times = [
                r["response_time"] for r in results if isinstance(r, dict) and r.get("success")
            ]
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


if __name__ == "__main__":
    asyncio.run(main())
