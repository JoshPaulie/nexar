"""Example demonstrating rate limiting functionality."""

import os
import time

from nexar import NexarClient, RateLimit, RateLimiter, RegionV4, RegionV5


def main():
    """Demonstrate rate limiting with the Nexar client."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Please set RIOT_API_KEY environment variable")
        return

    print("=== Rate Limiting Example ===\n")

    # Create client with default rate limiting (20 req/1s, 100 req/2min)
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )

    print("1. Default rate limiter configuration:")
    status = client.get_rate_limit_status()
    for limit_name, limit_info in status.items():
        print(
            f"   {limit_name}: {limit_info['requests']} requests per {limit_info['window_seconds']} seconds"
        )
    print()

    # Make a few API calls and show rate limit status
    print("2. Making API calls and monitoring rate limits:")
    for i in range(3):
        print(f"   Making API call {i + 1}...")
        start_time = time.time()

        try:
            account = client.get_riot_account("bexli", "bex")
            end_time = time.time()

            print(f"   → Success! Took {end_time - start_time:.3f}s")
            print(f"   → Account: {account.game_name}#{account.tag_line}")

            # Show current rate limit status
            status = client.get_rate_limit_status()
            for limit_name, limit_info in status.items():
                usage = limit_info["current_usage"]
                remaining = limit_info["remaining"]
                print(f"   → {limit_name}: {usage} used, {remaining} remaining")

        except Exception as e:
            print(f"   → Error: {e}")

        print()

    # Create a client with stricter rate limits to demonstrate waiting
    print("3. Testing with stricter rate limits (2 req/5s):")
    strict_rate_limiter = RateLimiter([RateLimit(requests=2, window_seconds=5)])

    strict_client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        rate_limiter=strict_rate_limiter,
    )

    # Make requests that will trigger rate limiting
    for i in range(3):
        print(f"   Making API call {i + 1}...")
        start_time = time.time()

        try:
            account = strict_client.get_riot_account("bexli", "bex")
            end_time = time.time()

            print(f"   → Success! Took {end_time - start_time:.3f}s")

            if end_time - start_time > 1:
                print("   → Rate limiting was applied (request was delayed)")

        except Exception as e:
            print(f"   → Error: {e}")

    print("\n4. Rate limiter status after strict testing:")
    status = strict_client.get_rate_limit_status()
    for limit_name, limit_info in status.items():
        usage = limit_info["current_usage"]
        remaining = limit_info["remaining"]
        reset_in = limit_info["reset_in_seconds"]
        print(
            f"   {limit_name}: {usage} used, {remaining} remaining, resets in {reset_in:.1f}s"
        )

    print("\n=== Rate Limiting Example Complete ===")


if __name__ == "__main__":
    main()
