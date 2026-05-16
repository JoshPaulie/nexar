"""Example: Configuring rate limits for production API keys."""

import asyncio
from nexar.client import NexarClient
from nexar.enums import Region


async def example_production_key() -> None:
    """Initialize client with production API key limits."""
    client = NexarClient(
        riot_api_key="your-production-api-key",
        app_rate_limits=((500, 10), (30000, 600)),
    )

    # Now the client uses production rate limits:
    # - 500 requests per 10 seconds (per region)
    # - 30,000 requests per 10 minutes (per region)

    await client.close()


async def example_custom_limits() -> None:
    """Set custom rate limits at construction time."""
    client = NexarClient(
        riot_api_key="your-api-key",
        app_rate_limits=((300, 5), (15000, 300)),
    )

    await client.close()


async def example_per_region_limits() -> None:
    """Demonstrate per-region rate limiting with production key."""
    client = NexarClient(
        riot_api_key="your-production-api-key",
        app_rate_limits=((500, 10), (30000, 600)),
    )

    # Production limits: 500 req/10s per region
    # Both NA1 and EUW1 can use their full 500/10s quota simultaneously

    # This uses 500/10s budget for NA1
    await client.get_riot_account("PlayerName", "NA1", Region.NA1)

    # This uses 500/10s budget for EUW1 (separate from NA1)
    await client.get_riot_account("PlayerName", "EUW1", Region.EUW1)

    # Each region can independently support 500 requests per 10 seconds

    await client.close()


if __name__ == "__main__":
    asyncio.run(example_production_key())
    asyncio.run(example_custom_limits())
