import asyncio
import logging
import time
from typing import Dict, List
import uuid

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RAGRetrieveConcurrencyTester:
    def __init__(self, base_url: str = "http://127.0.0.1:3333"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_rag_retrieve_request(self, request_id: int, dataset_id: str, query: str) -> Dict:
        """Send a rag_retrieve tool call request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": "rag_retrieve",
                "arguments": {
                    "dataset_id": dataset_id,
                    "query": query,
                    "top_k": 3,
                    "mode": "collapsed",
                },
            },
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
                    logger.info(f"RAG retrieve {request_id} succeeded in {response_time:.3f}s")
                else:
                    logger.warning(
                        f"RAG retrieve {request_id} failed with status {response.status}: {response_data}"
                    )

                return result
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"RAG retrieve {request_id} failed: {str(e)}")
            return {
                "request_id": request_id,
                "status": None,
                "response_time": response_time,
                "success": False,
                "error": str(e),
            }

    async def run_concurrent_rag_retrieve_calls(
        self, num_requests: int = 10, max_concurrent: int = 5, dataset_id: str = "test_dataset"
    ) -> List[Dict]:
        """Run multiple concurrent RAG retrieve requests"""
        logger.info(
            f"Starting concurrent RAG retrieve test: {num_requests} requests, max {max_concurrent} concurrent"
        )

        start_time = time.time()

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_rag_retrieve(request_id):
            async with semaphore:
                query = f"Test query {request_id} - {uuid.uuid4().hex[:8]}"
                return await self.send_rag_retrieve_request(request_id, dataset_id, query)

        # Create tasks for all requests
        tasks = [limited_rag_retrieve(i) for i in range(num_requests)]

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
        logger.info(f"Min response_time: {min_response_time:.3f}s")
        logger.info(f"Max response_time: {max_response_time:.3f}s")

        # Print detailed results
        print("\n=== DETAILED RESULTS ===")
        for result in results:
            if isinstance(result, dict):
                status = "SUCCESS" if result.get("success") else "FAILED"
                time_taken = result.get("response_time", 0)
                print(f"Request {result.get('request_id', 'N/A')}: {status} ({time_taken:.3f}s)")

        return results


async def main():
    """Main function to run the RAG retrieve concurrency test"""
    logger.info("Starting RAG Retrieve Concurrency Test")

    # You need to replace this with an actual dataset ID from your system
    # For testing purposes, you can use a dummy ID, but real tests should use actual datasets
    test_dataset_id = "test_dataset_id"  # Replace with actual dataset ID

    # Connect to 127.0.0.1 for local testing
    async with RAGRetrieveConcurrencyTester("http://127.0.0.1:3333") as tester:
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

        print("Running concurrent RAG retrieve requests test...")
        print(f"Target dataset: {test_dataset_id}")
        print(
            f"This test will send multiple concurrent rag_retrieve requests to test server concurrency."
        )
        print()

        # Run concurrency test
        # You can adjust these parameters:
        # - num_requests: Total number of requests to send
        # - max_concurrent: Maximum number of concurrent requests
        results = await tester.run_concurrent_rag_retrieve_calls(
            num_requests=10, max_concurrent=3, dataset_id=test_dataset_id
        )

        # Print summary
        print("\n=== RAG RETRIEVE CONCURRENCY TEST RESULTS ===")
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        print(f"Successful requests: {successful}/{len(results)}")

        if successful > 0:
            response_times = [
                r["response_time"] for r in results if isinstance(r, dict) and r.get("success")
            ]
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                print(f"Response time statistics:")
                print(f"  Average: {avg_time:.3f}s")
                print(f"  Minimum: {min_time:.3f}s")
                print(f"  Maximum: {max_time:.3f}s")

        # Check for any errors
        errors = [
            r
            for r in results
            if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success"))
        ]
        if errors:
            print(f"\nErrors found: {len(errors)}")
            for i, error in enumerate(errors[:3]):  # Show first 3 errors
                if isinstance(error, Exception):
                    print(f"  {i + 1}. Exception: {str(error)}")
                elif isinstance(error, dict):
                    print(f"  {i + 1}. Request failed: {error.get('error', 'Unknown error')}")
        else:
            print("\nNo errors found. All requests completed successfully!")

        print(f"\nTest completed. Processed {len(results)} requests concurrently.")


if __name__ == "__main__":
    asyncio.run(main())
