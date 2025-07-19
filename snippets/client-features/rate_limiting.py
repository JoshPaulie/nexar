import asyncio
import os
import sys

from nexar.client import NexarClient
from nexar.enums import Region

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("Please set RIOT_API_KEY environment variable")

client = NexarClient(
    riot_api_key=api_key,
    default_region=Region.NA1,
)


async def main() -> None:
    async with client:
        # --8<-- [start:basic-usage]
        # Rate limiting is automatically applied to all API calls
        account = await client.get_riot_account("bexli", "bex")
        # --8<-- [end:basic-usage]

        # --8<-- [start:custom-rate-limits]
        client_custom_limits = NexarClient(
            riot_api_key=api_key,
            default_region=Region.NA1,
            per_second_limit=(1, 1),  # Max of 1 request per second
            per_minute_limit=(10, 5),  # Max of 10 requests per 5 minutes
        )
        async with client_custom_limits:
            # Use client here
            pass
        # --8<-- [end:custom-rate-limits]

        # --8<-- [start:rate-limiting-vs-caching]
        # First call - fresh request, counts against rate limits
        account = await client.get_riot_account("bexli", "bex")  # Rate limited if needed

        # Subsequent calls - cached, no rate limiting
        account = await client.get_riot_account("bexli", "bex")  # Instant, no rate limit check
        account = await client.get_riot_account("bexli", "bex")  # Instant, no rate limit check

        # Different account - fresh request, rate limited
        other = await client.get_riot_account("Doublelift", "NA1")  # Rate limited if needed
        # --8<-- [end:rate-limiting-vs-caching]


if __name__ == "__main__":
    asyncio.run(main())