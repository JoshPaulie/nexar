# Rate Limiting

Nexar includes built-in rate limiting to comply with Riot's API limits and avoid 429 errors.

!!! Note

    If you hit a rate limit and Riot provides a `Retry-After` header, Nexar blocks the region for that duration and retries. If the header is missing or unparsable, a conservative 5-second block is applied instead.

## Default Rate Limits

By default, Nexar enforces Riot's personal-key limits:

- 20 requests per 1 second
- 100 requests per 2 minutes

These are enforced as sliding windows per region — the same rule Riot's edge applies — so the full quota is usable: 20 requests may fire in the first second, and short batches complete without artificial pacing.

## Basic Usage

Rate limiting is enabled automatically:

```python
--8<-- "client-features/rate_limiting.py:basic-usage"
```

## Custom Rate Limits

Configure custom app rate limits when creating the client:

```python
--8<-- "client-features/rate_limiting.py:custom-rate-limits"
```

## Production API Keys

If you have a Production API Key or can obtain higher limits, pass them directly:

```python
--8<-- "client-features/production_rate_limits.py:production-limits"
```

### Rate Limits per Region

Rate limits are enforced per region. Each region can simultaneously use its full quota:

```python
--8<-- "client-features/production_rate_limits.py:per-region-limits"
```

## How It Works

Nexar records the timestamp of every admitted request, per region, and admits the next request only when every rate window has a free slot. This mirrors Riot's documented sliding-window enforcement directly, so the limiter is exactly as accurate as the server's own count for a single process using one key.

Method and service rate limit headers are deliberately not tracked: the application window always binds first at every key tier (personal: 100/120s app vs. method limits like 2000/10s; production: 50/s app vs. 200/s method), so tracking them cannot change behavior.

The check-and-claim is synchronous, which is atomic on a single event loop — no locks, and concurrent callers never starve each other. Rate limit state is not persisted across restarts. Cached responses do not count against rate limits.

### Restarting a script (orientation)

A fresh client assumes empty windows, but Riot's ledger may be partially spent from a previous run. On the first fresh response for a region, Nexar reads Riot's own usage ledger (`X-App-Rate-Limit-Count`) and pre-fills the window log with the counted requests — so rerunning a script within two minutes cannot re-burst into a partially spent quota. Later responses hand the counts over too, but the limiter only orients once per region.

The seed cannot know the *age* of the counted requests, so each one is placed at the newest timestamp the counts allow (pessimistic about age): it can hold a slot slightly longer than strictly needed, never shorter. Cached responses never orient — they make no API call.

## Debugging Rate Limits

Rate limiter pacing decisions are logged at `DEBUG` level; 429s are logged at `WARNING`. See the [Logging](./logging.md) page to enable and configure Nexar's logging.

When the client is pacing, you'll see at `DEBUG`:

```
[nexar] Rate limit pacing for na1: waiting 1.21s
```

When a 429 arrives, at `WARNING`:

```
[nexar] 429 on attempt 1/5 for /lol/match/v5/matches/NA1_123 (region: na1). Blocking region for 3.0s
```

And once per region, at `INFO`, when a fresh client orients itself from the server's counts:

```
[nexar] Oriented na1 rate limits from server counts: {1: 5, 120: 90}
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
--8<-- "client-features/rate_limiting.py:rate-limiting-vs-caching"
```
