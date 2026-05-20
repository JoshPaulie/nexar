# Architecture

This document describes the internal architecture of Nexar using ASCII flow diagrams.

## Overview

```
                    +-------------------+
                    |    Your Code      |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |   NexarClient     |
                    |  (public API)     |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
    +--------------+  +-----------+  +------------+
    |  RateLimiter |  |   Cache   |  |  Models    |
    |  (leaky      |  | (SQLite / |  | (Player,   |
    |   buckets)   |  |  memory)  |  |  Match...) |
    +--------------+  +-----------+  +------------+
              |              |
              v              v
        Riot API Edge   aiohttp-client-cache
```

## Component: NexarClient

The `NexarClient` is the single entry point. Every API call flows through `_make_api_call()`, which orchestrates caching and rate limiting.

### Request flow — cache enabled

```
 CALLER
   |
   |  e.g. client.get_match("NA1_12345")
   v
 _make_api_call(endpoint, region, ...)
   |
   +--[1]--> _ensure_session()
   |           |  Creates CachedSession (SQLite or memory backend)
   |           |
   +--[2]--> _try_cache_response(url, headers, params)
   |           |
   |           +--- HIT --->  return cached data  (increments cache_hits)
   |           |
   |           +--- MISS ---> continue
   |
   +--[3]--> rate_limiter.acquire(region, method_id)
   |           |
   |           |  Blocks until app + method + service buckets
   |           |  all have capacity. Observes Retry-After blocks.
   |           |
   +--[4]--> session.get(url, headers, params)
   |           |
   |           +--- 200 OK ---> _record_success_response()
   |           |                   |  update_from_headers()
   |           |                   |  handle_response_errors()
   |           |                   +-- return response data
   |           |
   |           +--- 429 -----> retry loop
   |           |                   |  update_from_headers()
   |           |                   |  apply Retry-After blocking
   |           |                   +-- back to [3]
   |           |
   |           +--- 4xx/5xx --> raise RiotAPIError subclass
   |
   v
 RETURN data (dict parsed into model)
```

### Request flow — cache disabled

```
 CALLER
   |
   v
 _make_api_call(endpoint, region, ...)
   |
   +--[1]--> _ensure_session()
   |           |  Creates plain aiohttp.ClientSession
   |           |
   +--[2]--> _try_cache_response()  →  always returns None
   |
   +--[3]--> rate_limiter.acquire(region, method_id)
   |
   +--[4]--> session.get(url, headers, params)
   |           |
   |           +--- 200 OK ---> return response data
   |           +--- 429 -----> retry loop (up to 5 attempts)
   |           +--- error ---> raise
   |
   v
 RETURN data
```

### Retry loop detail

```
 for attempt in range(max_retries=5):
     |
     +-- acquire rate limit slot
     |
     +-- GET request
     |     |
     |     +--- 200/304 ---> SUCCESS (return)
     |     |
     |     +--- 429 -------> update_from_headers()
     |     |                  retries += 1
     |     |                  continue loop
     |     |
     |     +--- network err-> retries += 1
     |                        exponential backoff: 2^attempt seconds
     |                        if last attempt: raise RiotAPIError
     |
     +-- if loop exhausted: raise RateLimitError
```

## Component: RateLimiter

The `RateLimiter` uses `aiolimiter.AsyncLimiter` (leaky bucket algorithm) to enforce Riot's rate limits across three tiers.

### Bucket hierarchy

```
                        +----------------------+
                        |    APP LIMITS        |  <-- static, from config
                        | e.g. 20/1s, 100/120s |
                        +----------+-----------+
                                   |
                        +----------+-----------+
                        |   SERVICE LIMITS     |  <-- dynamic, from headers
                        | per-region, per-svc  |
                        +----------+-----------+
                                   |
                        +----------+-----------+
                        |   METHOD LIMITS      |  <-- dynamic, from headers
                        | per-region, per-method|
                        +----------------------+
```

### acquire() flow

```
 rate_limiter.acquire(region="na1", method="league-v4")
   |
   +-- acquire region lock (asyncio.Lock)
   |
   +-- LOOP:
   |     |
   |     +-- calc_block_wait: are we in a Retry-After penalty?
   |     |
   |     +-- collect_buckets(region, method)
   |     |     |  app buckets        (static, per-region)
   |     |     |  + service buckets  (dynamic, matching region)
   |     |     |  + method buckets   (dynamic, matching region+method)
   |     |
   |     +-- all have_capacity()?
   |     |     |
   |     |     +--- YES + no block --> break loop
   |     |     +--- NO  ------------> sleep(max(block_wait, 0.1s)),
   |     |                              log reason, loop again
   |
   +-- acquire() on every collected bucket (atomic under lock)
   |
   v
 REQUEST ALLOWED
```

### 429 handling flow

```
 update_from_headers(headers, region, method)
   |
   +-- Retry-After present?
   |     |
   |     +--- YES --> _apply_retry_after_block()
   |     |              |
   |     |              +-- detect rate limit type from headers
   |     |              |     |  "application" -> block app buckets
   |     |              |     |  "method"      -> block method buckets
   |     |              |     |  "service"     -> block service buckets
   |     |              |     |  (absent)      -> block ALL region buckets
   |     |              |
   |     |              +-- if service/method 429 lacks its own limit
   |     |                  header, also block app buckets (cascading)
   |     |
   +-- Parse X-Method-Rate-Limit + X-Method-Rate-Limit-Count
   |     |  Create/replace dynamic method AsyncLimiter
   |     |  Key: method_{region}_{method}_{limit}:{window}
   |
   +-- Parse X-Service-Rate-Limit + X-Service-Rate-Limit-Count
         |  Create/replace dynamic service AsyncLimiter
         |  Key: service_{region}_{limit}:{window}
```

### Safety margin

```
 Effective limit = floor(server_limit * (1 - safety_margin))

 Example: server says 500 req / 10s, safety_margin = 0.01
          → effective = floor(500 * 0.99) = 495 req / 10s

 This reserves 1% headroom to avoid hitting the exact boundary
 where Riot might issue a 429.
```

## Component: Cache

Nexar uses `aiohttp-client-cache` for transparent HTTP caching.

### Backend selection

```
 CacheConfig
   |
   +-- backend = "sqlite" (default)
   |     |
   |     +-- SQLiteBackend
   |     |     cache_dir: ~/.nexar/ (or custom)
   |     |     file:      {cache_name}.sqlite
   |     |
   |     +-- Persistent across restarts
   |
   +-- backend = "memory"
         |
         +-- DictCache
         |     stored in-process, ephemeral
         |
         +-- Lost on process exit
```

### Smart endpoint TTLs

```
 Endpoint pattern                                    TTL
 ──────────────────────────────────────────────────  ──────────
 */lol/match/v5/matches/*                            forever
 */lol/league/v4/entries/by-puuid/*                  5 minutes
 */lol/match/v5/matches/by-puuid/*/ids               1 minute
 */riot/account/v1/accounts/by-riot-id/*             24 hours
 */lol/summoner/v4/summoners/by-puuid/*              24 hours
 (anything else)                                     1 hour (default)
```

### Cache lookup flow

```
 _try_cache_response(url, headers, params)
   |
   +-- session is CachedSession?  ---- NO ---> return None
   |
   +-- build cache key from (GET, url, params, headers)
   |
   +-- cache.get_response(cache_key)
   |     |
   |     +--- HIT + response.ok --> return response.json()
   |     |                          cache_hits += 1
   |     |
   |     +--- MISS or expired ----> return None
```

### When cache is disabled

```
 CacheConfig(enabled=False)  →  NO_CACHE_CONFIG

 _ensure_session() creates plain aiohttp.ClientSession

 _try_cache_response() short-circuits (not a CachedSession)

 All requests go directly to Riot API (still rate limited)
```

## Component: Models

API responses are parsed into typed Python objects. Each model class has a `from_api_response()` factory.

```
 JSON response (dict)
   |
   v
 Model.from_api_response(data)
   |
   +-- Extracts fields
   +-- Converts nested objects to sub-models
   +-- Validates types
   |
   v
 Typed dataclass (Player, Match, LeagueEntry, Summoner, etc.)
```

### High-level Player convenience

```
 NexarClient.get_player(game_name="bexli", tag_line="bex")
   |
   +-- Resolves region from arg or default
   |
   +-- Player.create()
   |     |
   |     +-- get_riot_account()  →  RiotAccount (PUUID)
   |     +-- get_summoner_by_puuid()  →  Summoner (level, icon)
   |     +-- get_league_entries_by_puuid()  →  list[LeagueEntry]
   |
   v
 Player object with all data pre-fetched
```

## Full request lifecycle (end-to-end)

```
 User calls client.get_match("NA1_12345")
   |
   v
 NexarClient._make_api_call("/lol/match/v5/matches/NA1_12345", "na1", "americas")
   |
   +-- Build URL: https://americas.api.riotgames.com/lol/match/v5/matches/NA1_12345
   |
   +-- _ensure_session() → CachedSession (or ClientSession if no cache)
   |
   +-- _try_cache_response()
   |     |
   |     +--- HIT ---> return cached JSON ──────────────────────┐
   |     |                                                        |
   |     +--- MISS ---> continue                                  |
   |                                                              |
   +-- rate_limiter.acquire("na1", "match-v5")                    |
   |     |  Checks app buckets: 20/1s + 100/120s                  |
   |     |  Checks service buckets (if any from prior requests)   |
   |     |  Checks method buckets (if any)                        |
   |     |  Blocks if needed, then acquires                       |
   |                                                              |
   +-- session.get(url) ─────────────────────────────────────────┐|
   |     |                                                        ||
   |     +--- 200 ---> _record_success_response()                 ||
   |     |     |  update_from_headers() - sync rate limit state   ||
   |     |     |  handle_response_errors() - raise if not ok      ||
   |     |     |  return JSON ────────────────────────────────────┘|
   |     |                                                         |
   |     +--- 429 ---> retry loop                                  |
   |     +--- 4xx ---> raise NotFoundError / UnauthorizedError     |
   |                                                               |
   v                                                               v
 Match.from_api_response(data)                              Cached response
   |
   v
 Match object returned to caller
```
