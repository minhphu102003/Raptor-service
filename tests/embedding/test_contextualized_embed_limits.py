"""
Test script to verify actual limits of Voyage AI contextualized_embed function
This focuses specifically on the contextualized_embed function with various payload sizes.
"""

import asyncio
import os
import time
from typing import List, Tuple

import voyageai


class VoyageContextualEmbedTest:
    def __init__(self, api_key: str, model: str = "voyage-context-3"):
        self.api_key = api_key
        self.model = model
        self.client = voyageai.AsyncClient(api_key=api_key)

    async def close(self):
        """Close the client connection"""
        # The AsyncClient doesn't have a close method, so we just let it be garbage collected
        pass

    def create_test_texts(self, count: int, text_length: int = 100) -> List[str]:
        """Create test texts for embedding"""
        return [
            f"This is test text number {i} with approximately {text_length} characters for rate limit testing. "
            * (text_length // 100 + 1)
            for i in range(count)
        ]

    async def test_single_request_limits(
        self, text_count: int, text_length: int = 100
    ) -> Tuple[bool, int, str]:
        """
        Test a single request with specified parameters
        Returns: (success, token_estimate, error_message)
        """
        texts = self.create_test_texts(text_count, text_length)

        try:
            # Make the actual API call
            response = await self.client.contextualized_embed(
                inputs=[texts], model=self.model, input_type="document"
            )

            # Estimate tokens (rough approximation)
            total_chars = sum(len(text) for text in texts)
            token_estimate = total_chars // 4  # Rough estimation

            return True, token_estimate, "Success"

        except Exception as e:
            return False, 0, f"Error: {e}"

    async def test_batch_requests(
        self, batch_size: int, requests_per_batch: int, delay: float = 1.0
    ) -> dict:
        """
        Test batch requests to determine rate limits
        """
        print(f"Testing batch: {requests_per_batch} requests with {batch_size} texts each")

        start_time = time.time()
        results = {"successful_requests": 0, "total_tokens": 0, "errors": [], "duration": 0}

        tasks = []
        for i in range(requests_per_batch):
            task = self.test_single_request_limits(batch_size)
            tasks.append(task)

            # Add small delay between requests
            await asyncio.sleep(0.05)

        # Execute all requests
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                results["errors"].append(str(response))
            elif isinstance(response, tuple) and response[0]:  # Success
                results["successful_requests"] += 1
                results["total_tokens"] += response[1]
            elif isinstance(response, tuple):  # Failure
                results["errors"].append(response[2])

        results["duration"] = time.time() - start_time
        return results

    async def find_max_request_size(self) -> dict:
        """Find the maximum request size before hitting limits"""
        print("Finding maximum request size...")

        # Test with increasing text counts
        text_counts = [1, 10, 50, 100, 200, 500, 1000]
        results = {}

        for count in text_counts:
            print(f"Testing with {count} texts...")
            success, tokens, message = await self.test_single_request_limits(count)
            results[count] = {"success": success, "tokens": tokens, "message": message}
            print(f"  Result: {message}")

            # If we hit a limit, stop increasing
            if not success and "rate" in message.lower():
                break

            # Small delay between tests
            await asyncio.sleep(1)

        return results

    async def test_rate_limits_over_time(self, duration_minutes: int = 2) -> dict:
        """Test rate limits over a period of time"""
        print(f"Testing rate limits over {duration_minutes} minutes...")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        requests_made = 0
        successful_requests = 0
        total_tokens = 0
        errors = []

        while time.time() < end_time:
            success, tokens, message = await self.test_single_request_limits(
                10
            )  # 10 texts per request
            requests_made += 1

            if success:
                successful_requests += 1
                total_tokens += tokens
                print(f"Request {requests_made}: Success ({tokens} tokens)")
            else:
                errors.append(message)
                print(f"Request {requests_made}: {message}")

                # If rate limited, wait a bit before retrying
                if "rate" in message.lower():
                    await asyncio.sleep(5)

            # Small delay between requests
            await asyncio.sleep(0.5)

        duration = time.time() - start_time
        return {
            "duration": duration,
            "requests_made": requests_made,
            "successful_requests": successful_requests,
            "total_tokens": total_tokens,
            "errors": errors,
            "rpm": requests_made / (duration / 60),
            "tpm": total_tokens / (duration / 60),
        }


async def main():
    """Main function to run all tests"""
    api_key = os.getenv("VOYAGEAI_KEY")

    if not api_key:
        print("ERROR: Please set the VOYAGEAI_KEY environment variable")
        return

    print("Voyage AI contextualized_embed Rate Limit Verification")
    print("=" * 60)
    print(f"Using API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print()

    tester = VoyageContextualEmbedTest(api_key)

    try:
        # Test 1: Find maximum request size
        print("1. Finding Maximum Request Size")
        print("-" * 30)
        max_size_results = await tester.find_max_request_size()
        print("Max size results:", max_size_results)
        print()

        # Wait a bit before next test
        print("Waiting 10 seconds...")
        await asyncio.sleep(10)

        # Test 2: Rate limits over time
        print("2. Testing Rate Limits Over Time")
        print("-" * 30)
        rate_limit_results = await tester.test_rate_limits_over_time(2)  # 2 minutes
        print("Rate limit results:")
        print(f"  Duration: {rate_limit_results['duration']:.2f} seconds")
        print(f"  Requests made: {rate_limit_results['requests_made']}")
        print(f"  Successful requests: {rate_limit_results['successful_requests']}")
        print(f"  Total tokens: {rate_limit_results['total_tokens']}")
        print(f"  Requests per minute: {rate_limit_results['rpm']:.2f}")
        print(f"  Tokens per minute: {rate_limit_results['tpm']:.0f}")
        print(f"  Errors: {len(rate_limit_results['errors'])}")
        if rate_limit_results["errors"]:
            print(f"  First error: {rate_limit_results['errors'][0]}")
        print()

        # Test 3: Batch requests
        print("3. Testing Batch Requests")
        print("-" * 30)
        batch_results = await tester.test_batch_requests(50, 10)  # 10 requests with 50 texts each
        print("Batch results:")
        print(f"  Duration: {batch_results['duration']:.2f} seconds")
        print(f"  Successful requests: {batch_results['successful_requests']}")
        print(f"  Total tokens: {batch_results['total_tokens']}")
        print(f"  Errors: {len(batch_results['errors'])}")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
