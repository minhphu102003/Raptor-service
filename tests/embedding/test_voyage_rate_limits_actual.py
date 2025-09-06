"""
Test script to verify actual rate limits of Voyage AI contextualized_embed function
This script makes actual API calls to test the documented limits.
"""

import asyncio
import os
import time
from typing import List

import voyageai

# Test configuration
MODEL = "voyage-context-3"
TEST_API_KEY = os.getenv("VOYAGEAI_KEY")
REQUESTS_TO_TEST = 100  # Number of requests to send for testing
CHUNK_SIZE = 100  # Number of texts per request


def create_test_texts(count: int) -> List[str]:
    """Create test texts for embedding"""
    return [f"This is test text number {i} for rate limit testing." for i in range(count)]


async def test_tpm_limit():
    """Test the actual TPM (Tokens Per Minute) limit"""
    if not TEST_API_KEY:
        print("ERROR: VOYAGEAI_KEY environment variable not set")
        return

    client = voyageai.AsyncClient(api_key=TEST_API_KEY)

    print(f"Testing TPM limit for model: {MODEL}")
    print(f"Making {REQUESTS_TO_TEST} requests with {CHUNK_SIZE} texts each...")

    start_time = time.time()
    successful_requests = 0
    total_tokens = 0

    try:
        for i in range(REQUESTS_TO_TEST):
            texts = create_test_texts(CHUNK_SIZE)

            try:
                # Make the actual API call
                response = await client.contextualized_embed(
                    inputs=[texts], model=MODEL, input_type="document"
                )

                successful_requests += 1
                # Estimate tokens (rough approximation)
                tokens_in_request = len(" ".join(texts)) // 4  # Rough estimation
                total_tokens += tokens_in_request

                print(f"Request {i + 1}/{REQUESTS_TO_TEST}: Success - {tokens_in_request} tokens")

                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"Request {i + 1}/{REQUESTS_TO_TEST}: Error - {e}")
                # Check if it's a rate limit error
                if "rate" in str(e).lower():
                    print(f"    This appears to be a rate limit error")
                    break
                continue

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n=== TPM Test Results ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Successful requests: {successful_requests}")
        print(f"Total estimated tokens: {total_tokens}")
        print(f"Tokens per minute: {total_tokens / (duration / 60):.0f}")
        print(f"Requests per minute: {successful_requests / (duration / 60):.0f}")

    finally:
        # The AsyncClient doesn't have a close method, so we just let it be garbage collected
        pass


async def test_rpm_limit():
    """Test the actual RPM (Requests Per Minute) limit"""
    if not TEST_API_KEY:
        print("ERROR: VOYAGEAI_KEY environment variable not set")
        return

    client = voyageai.AsyncClient(api_key=TEST_API_KEY)

    print(f"Testing RPM limit for model: {MODEL}")
    print(f"Making {REQUESTS_TO_TEST} requests...")

    start_time = time.time()
    successful_requests = 0

    try:
        for i in range(REQUESTS_TO_TEST):
            # Small request to focus on request count rather than token count
            texts = ["This is a small test text for RPM testing."]

            try:
                # Make the actual API call
                response = await client.contextualized_embed(
                    inputs=[texts], model=MODEL, input_type="document"
                )

                successful_requests += 1
                print(f"Request {i + 1}/{REQUESTS_TO_TEST}: Success")

                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"Request {i + 1}/{REQUESTS_TO_TEST}: Error - {e}")
                # Check if it's a rate limit error
                if "rate" in str(e).lower():
                    print(f"    This appears to be a rate limit error")
                    break
                continue

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n=== RPM Test Results ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Successful requests: {successful_requests}")
        print(f"Requests per minute: {successful_requests / (duration / 60):.0f}")

    finally:
        # The AsyncClient doesn't have a close method, so we just let it be garbage collected
        pass


async def main():
    """Main function to run all tests"""
    print("Voyage AI Rate Limit Verification Script")
    print("=" * 50)

    if not TEST_API_KEY:
        print("ERROR: Please set the VOYAGEAI_KEY environment variable")
        return

    print(
        f"Using API Key: {TEST_API_KEY[:8]}...{TEST_API_KEY[-4:] if len(TEST_API_KEY) > 12 else ''}"
    )
    print()

    # Test TPM limit
    print("1. Testing TPM (Tokens Per Minute) Limit")
    print("-" * 40)
    await test_tpm_limit()
    print()

    # Wait a bit before next test
    print("Waiting 10 seconds before next test...")
    await asyncio.sleep(10)

    # Test RPM limit
    print("2. Testing RPM (Requests Per Minute) Limit")
    print("-" * 40)
    await test_rpm_limit()


if __name__ == "__main__":
    asyncio.run(main())
