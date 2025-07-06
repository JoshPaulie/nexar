"""Test async rate limiting with cache disabled."""

import asyncio
import os
import sys
import time

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.rate_limiter import RateLimit, RateLimiter


async def test_rate_limiting_no_cache() -> None:
    """Test that async rate limiting works correctly with caching disabled."""
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
        cache_config=NO_CACHE_CONFIG,  # Disable caching
        rate_limiter=rate_limiter,
    ) as client:
        print("Testing async rate limiting (cache disabled)...")
        print("Rate limit: 2 requests per 5 seconds")

        start_time = time.time()

        # Make multiple requests to different endpoints to avoid any caching
        print("Making request 1...")
        await client.get_riot_account("bexli", "bex")
        print("Making request 2...")
        await client.get_riot_account("bexli", "bex")
        print("Making request 3 (should be rate limited)...")
        await client.get_riot_account("bexli", "bex")

        end_time = time.time()
        elapsed = end_time - start_time

        # With 2 requests per 5 seconds, the third request should be delayed
        expected_min_duration = 5.0

        print(f"Completed 3 requests in {elapsed:.2f} seconds")
        if elapsed >= expected_min_duration:
            print("Rate limiting worked correctly!")
        else:
            print("Rate limiting may not be working")


if __name__ == "__main__":
    asyncio.run(test_rate_limiting_no_cache())
