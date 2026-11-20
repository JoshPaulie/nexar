# Cache configuration

Responses are cached by default (SQLite under `~/.nexar/`, one-hour default TTL,
per-endpoint smart TTLs, 200-only). Pass `cache_config=NO_CACHE_CONFIG` to
disable, or build your own `CacheConfig`.

::: nexar.cache.CacheConfig

::: nexar.cache.DEFAULT_CACHE_CONFIG

::: nexar.cache.NO_CACHE_CONFIG

::: nexar.cache.ttl

::: nexar.cache.create_cache_backend

::: nexar.cache.NexarSQLiteBackend
