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
-8<-- "client-features/rate_limiting.py:basic-usage"
```

## Custom Rate Limits

You can configure custom rate limits if needed:

```python
-8<-- "client-features/rate_limiting.py:custom-rate-limits"
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
-8<-- "client-features/rate_limiting.py:rate-limiting-vs-caching"
```