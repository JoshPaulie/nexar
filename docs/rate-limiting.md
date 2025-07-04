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
from nexar import NexarClient, RegionV4, RegionV5

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS
)

# Rate limiting is automatically applied to all API calls
account = client.get_riot_account("bexli", "bex")
```

## Custom Rate Limits

You can configure custom rate limits if needed:

```python
from nexar import NexarClient, RateLimit, RateLimiter, RegionV4, RegionV5

# Create custom rate limiter
custom_limiter = RateLimiter([
    RateLimit(requests=10, window_seconds=1),    # 10 per second
    RateLimit(requests=50, window_seconds=120),  # 50 per 2 minutes
])

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    rate_limiter=custom_limiter
)
```

## Monitoring Rate Limit Status

You can check your current rate limit usage:

```python
# Get current rate limit status
status = client.get_rate_limit_status()

for limit_name, info in status.items():
    print(f"{limit_name}: {info['current_usage']}/{info['requests']} used")
    print(f"  Remaining: {info['remaining']}")
    print(f"  Window: {info['window_seconds']} seconds")
    print(f"  Reset in: {info['reset_in_seconds']:.1f} seconds")
```

## Resetting Rate Limiter

You can reset the rate limiter state if needed:

```python
# Reset rate limiter (clears all tracked requests)
client.reset_rate_limiter()
```

## How It Works

- **Automatic Enforcement**: Before each API call, Nexar checks if you're within rate limits
- **Smart Waiting**: If you hit a rate limit, Nexar automatically waits the minimum required time
- **Multiple Windows**: Supports multiple rate limit windows (e.g., per-second and per-minute limits)
- **Sliding Windows**: Uses sliding time windows for accurate rate limiting
- **No Manual Management**: You don't need to manage rate limiting manually - just make API calls normally
- **Comprehensive Logging**: Detailed logging at DEBUG level, INFO level messages when rate limits are hit

## Logging

The rate limiter provides detailed logging to help you understand what's happening:

### DEBUG Level Logging
```python
from nexar import configure_logging
import logging

# Enable debug logging to see detailed rate limit information
configure_logging(logging.DEBUG)
```

Debug logs include:
- Rate limiter initialization with configured limits
- Current usage for each rate limit before each request
- Cleanup of expired requests
- Request recording timestamps

### INFO Level Logging
```python
configure_logging(logging.INFO)  # Default level
```

Info logs include:
- When rate limits are hit and how long the wait will be
- When rate limit waits complete and requests proceed

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

Rate limiting and caching work together:

1. **Caching** reduces the number of actual API calls by returning cached responses
2. **Rate limiting** ensures that when API calls are made, they don't exceed Riot's limits

Cached responses don't count against rate limits since no actual API request is made.
