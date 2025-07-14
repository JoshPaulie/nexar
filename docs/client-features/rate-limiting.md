# Rate Limiting

Nexar includes built-in rate limiting to ensure your application complies with Riot's API rate limits and avoids getting rate limited.

## Default Rate Limits

By default, Nexar enforces the following rate limits:

- **20 requests per 1 second**
- **100 requests per 2 minutes**

These are the standard Riot API limits for most applications.

## Basic Usage

Rate limiting is enabled automatically when you create a `NexarClient`:

```python
import asyncio
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

client = NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS
)

async def main() -> None:
    async with client:
        # Rate limiting is automatically applied to all API calls
        account = await client.get_riot_account("bexli", "bex")

if __name__ == "__main__":
    asyncio.run(main())
```

## Custom Rate Limits

You can configure custom rate limits if needed:

```python
import asyncio
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

client = NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS
        per_second_limit=(1, 1), # Max of 1 request per second
        per_minute_limit=(10, 5), # Max of 10 requests per 5 minutes
)


async def main() -> None:
    async with client:
        # Use client here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

## How It Works

Nexar automatically enforces Riot's API rate limits using the `aiolimiter` library. It intelligently waits when limits are hit and supports multiple rate limit windows. You don't need to manage rate limiting manually. Cached responses do not count against rate limits.

## Logging

The rate limiter provides detailed logging to help you understand its behavior. You can configure logging levels using `configure_logging`.

### Example Log Output
```
[nexar] Rate limiter initialized with 2 limits:
[nexar]   Limit 1: 20 requests per 1s
[nexar]   Limit 2: 100 requests per 120s
[nexar] Limit 1: 19/20 used, 1 remaining
[nexar] Limit 2: 45/100 used, 55 remaining
[nexar] Rate limit hit! Limit 1 (20 req/1s) - waiting 0.85 seconds
[nexar] Rate limit wait complete - proceeding with request
```

## Rate Limiting vs Caching

Rate limiting and caching work together intelligently:

1. **Cached responses** don't count against rate limits since no actual API request is made
2. **Fresh requests** are subject to rate limiting to ensure compliance with Riot's limits
3. **Cache hits** are instant and don't consume any rate limit quota
4. **Cache misses** trigger rate limiting before making the actual API call

This means you can make the same API call repeatedly without worrying about rate limits if the response is cached. Only unique requests or expired cache entries will consume your rate limit quota.

### Example
```python
import asyncio
from nexar import NexarClient, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # First call - fresh request, counts against rate limits
        account = await client.get_riot_account("bexli", "bex")  # Rate limited if needed

        # Subsequent calls - cached, no rate limiting
        account = await client.get_riot_account("bexli", "bex")  # Instant, no rate limit check
        account = await client.get_riot_account("bexli", "bex")  # Instant, no rate limit check

        # Different account - fresh request, rate limited
        other = await client.get_riot_account("Doublelift", "NA1")  # Rate limited if needed

if __name__ == "__main__":
    asyncio.run(main())
```
