# Rate Limiting

Nexar includes built-in rate limiting to comply with Riot's API limits and avoid 429 errors.

!!! Note

    If you hit a rate limit and Riot provides a `Retry-After` header, Nexar will wait the required duration and continue.

## Default Rate Limits

By default, Nexar enforces:

- 20 requests per 1 second
- 100 requests per 2 minutes

These are the default rates for Riot personal API keys.

## Basic Usage

Rate limiting is enabled automatically:

```python
-8<-- "client-features/rate_limiting.py:basic-usage"
```

## Custom Rate Limits

Configure custom app rate limits when creating the client:

```python
-8<-- "client-features/rate_limiting.py:custom-rate-limits"
```

## Production API Keys

If you have a Production API Key or can obtain higher limits, pass them directly:

```python
client = NexarClient(
    riot_api_key="your-prod-key",
    app_rate_limits=((500, 10), (30000, 600)), # 500/10s and 30,000/10m
)
```

### Rate Limits per Region

Rate limits are enforced per region. Each region can simultaneously use its full quota:

```python
# With production limits (500 req/10s per region)
await client.get_riot_account("Doublelift", "NA1", region=Region.NA1)  # Uses NA1 budget
await client.get_riot_account("G2 Wunder", "EUW", region=Region.EUW1)  # Uses EUW1 budget
```

## Safety Margin

By default, Nexar reserves a 1% buffer from every rate limit bucket to avoid hitting Riot's exact boundary and getting 429 errors. For example, with a 500 req/10s limit, the effective limit is 495 req/10s.


You can adjust or disable it:

```python
client = NexarClient(
    riot_api_key="your-key",
    rate_limit_safety_margin=0.05,  # Reserve 5%
)

# Or disable entirely (At your own risk)
client = NexarClient(
    riot_api_key="your-key",
    rate_limit_safety_margin=0.0,
)
```

## How It Works

Nexar uses a leaky bucket rate limiter backed by `aiolimiter`. It parses Riot response headers (`X-App-Rate-Limit`, `X-Method-Rate-Limit`, `X-Service-Rate-Limit`) to create dynamic limit buckets and handles 429 responses with `Retry-After` blocking.

The effective limit for each bucket is `max(1, floor(limit × (1 - safety_margin)))`, rounded down to avoid overstepping and ensuring the limit never drops to 0. Rate limits are enforced per region with per-region locking to prevent race conditions.

Rate limits are not persisted across restarts. Cached responses do not count against rate limits.

## Debugging Rate Limits

Rate limiter decisions are logged at `INFO` level. See the [Logging](./logging.md) page to enable and configure Nexar's logging.

When rate limits are hit, you'll see messages like:

```
[nexar] Rate limit FULL for na1/api_get_account. Sleeping 0.85s  (INFO)
[nexar] Rate limit BLOCKED (429) for na1/api_get_account. Sleeping 1.23s  (WARNING)
```

## Rate Limiting vs Caching

Rate limiting and caching work together:

1. Cached responses don't count against rate limits.
2. Fresh requests are subject to rate limiting.
3. Cache hits are instant and don't consume quota.
4. Cache misses trigger rate limiting before the API call.

Repeat API calls won't hit rate limits if the response is cached.

### Example
```python
-8<-- "client-features/rate_limiting.py:rate-limiting-vs-caching"
```
