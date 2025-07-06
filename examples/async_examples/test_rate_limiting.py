"""Test async rate limiting functionality."""

import asyncio
import os
import sys
import time

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.rate_limiter import RateLimit, RateLimiter


async def test_rate_limiting() -> None:
    """Test that async rate limiting works correctly."""
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create a very restrictive rate limiter for testing
    rate_limiter = RateLimiter(
        [
            RateLimit(requests=2, window_seconds=5),  # Only 2 requests per 5 seconds
        ]
    )

    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        rate_limiter=rate_limiter,
    ) as client:
        print("Testing async rate limiting...")
        print("Rate limit: 2 requests per 5 seconds")

        start_time = time.time()

        # Make multiple requests that should trigger rate limiting
        tasks = []
        for i in range(5):
            task = client.get_riot_account("bexli", "bex")
            tasks.append(task)
            print(f"Queued request {i + 1}")

        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = end_time - start_time

        # With 2 requests per 5 seconds, 5 requests should take at least 10 seconds
        expected_min_duration = 10.0

        print(f"Completed {len(results)} requests in {elapsed:.2f} seconds")
        if elapsed >= expected_min_duration:
            print("Rate limiting worked correctly!")
        else:
            print("Rate limiting may not be working")

        # Verify all requests returned the same account
        for i, account in enumerate(results):
            print(f"Request {i + 1}: {account.game_name}#{account.tag_line}")


if __name__ == "__main__":
    asyncio.run(test_rate_limiting())
