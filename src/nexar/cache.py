"""Cache configuration for the Nexar SDK."""

from __future__ import annotations

import hashlib
import logging
import pickle
import sqlite3
from dataclasses import dataclass
from http.cookies import CookieError
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from aiohttp import RequestInfo
from aiohttp_client_cache.backends.base import CacheBackend
from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from multidict import CIMultiDict, CIMultiDictProxy

if TYPE_CHECKING:
    from datetime import datetime

    from aiohttp import ClientResponse
    from aiohttp.typedefs import StrOrURL
    from aiohttp_client_cache.cache_control import ExpirationTime
    from aiohttp_client_cache.response import CachedResponse

logger = logging.getLogger("nexar.cache")

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "CacheConfig",
    "NexarSQLiteBackend",
    "create_cache_backend",
    "ttl",
]


def ttl(*, minutes: int = 0, hours: int = 0, days: int = 0) -> int:
    """Helper to convert minutes/hours to seconds for TTL values."""
    return minutes * 60 + hours * 3600 + days * 86400


# Per-endpoint TTLs for data that has predictable freshness characteristics.
# Match detail is immutable once finished → cached forever.
# Account/summoner lookup data rarely changes → cached 24 hours.
# League ladders (apex lists, division pages, by-puuid entries) shift with every
# ranked game → cached 5 minutes.
# Champion mastery changes only through play → cached 30 minutes.
# Match ID lists change as new matches are played → cached 1 minute.
# Champion rotations refresh on the weekly/patch cycle → cached 1 day.
# Platform status is near-realtime incident data → cached 1 minute.
# Challenge configs and percentiles are catalog data on the patch cycle → 6 hours.
# Challenge leaderboards shift live with every game → cached 5 minutes.
# Player challenge progress changes only through play → cached 30 minutes.
# Order matters: more specific patterns must come first (first match wins).
_SMART_ENDPOINT_TTLS: dict[str, ExpirationTime] = {
    "*/lol/match/v5/matches/by-puuid/*/ids": ttl(minutes=1),
    "*/lol/league/v4/entries/by-puuid/*": ttl(minutes=5),
    # Division ladders: this glob needs two literal slashes after /entries/,
    # which by-puuid URLs never have (they carry one), so it cannot shadow the
    # row above, verified through the library's own url_match, not just
    # assumed. The page query parameter is not part of the URL the library
    # matches patterns against.
    "*/lol/league/v4/entries/*/*/*": ttl(minutes=5),
    "*/lol/league/v4/challengerleagues/*": ttl(minutes=5),
    "*/lol/league/v4/grandmasterleagues/*": ttl(minutes=5),
    "*/lol/league/v4/masterleagues/*": ttl(minutes=5),
    "*/lol/league-exp/v4/entries/*/*/*": ttl(minutes=5),
    "*/lol/champion-mastery/v4/champion-masteries/by-puuid/*": ttl(minutes=30),
    "*/lol/champion-mastery/v4/scores/by-puuid/*": ttl(minutes=30),
    # Challenge family: the two catalog ops and their by-id twins ride together.
    # The literal config/percentiles globs cannot shadow the by-id ones. They
    # carry no wildcard before their final segment, so the by-id URLs' extra
    # segment cannot be absorbed. (The library's matcher crosses path
    # separators freely, verified through its own url_match.)
    "*/lol/challenges/v1/challenges/config": ttl(hours=6),
    "*/lol/challenges/v1/challenges/*/config": ttl(hours=6),
    "*/lol/challenges/v1/challenges/percentiles": ttl(hours=6),
    "*/lol/challenges/v1/challenges/*/percentiles": ttl(hours=6),
    "*/lol/challenges/v1/challenges/*/leaderboards/by-level/*": ttl(minutes=5),
    "*/lol/challenges/v1/player-data/*": ttl(minutes=30),
    # aiohttp-client-cache's never-expire sentinel. A None value here is skipped
    # by the library's coalesce (indistinguishable from no pattern match), which
    # silently resolved immutable match URLs to the 1-hour session default.
    "*/lol/match/v5/matches/*": -1,
    "*/lol/platform/v3/champion-rotations": ttl(days=1),
    "*/lol/status/v4/platform-data": ttl(minutes=1),
    "*/riot/account/v1/accounts/by-riot-id/*": ttl(days=1),
    "*/lol/summoner/v4/summoners/by-puuid/*": ttl(days=1),
}


def _api_key_fingerprint(api_key: str) -> str:
    """A stable one-way namespace tag for an API key. Never the key itself."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


class _KeyNamespacedBackend(CacheBackend):
    """CacheBackend whose rows are namespaced by the API key that fetched them.

    Riot auth travels in a header the library's cache keys ignore, so two
    clients with different keys reading one sqlite file would serve each
    other's rows: a wrong or rotated key would silently read the previous
    key's data, and because Riot encrypts PUUIDs per project, a row carrying
    PUUIDs is unusable to the other key rather than merely stale. Every key
    this backend builds (the client's manual read and the session's own
    interception alike) is prefixed with a fingerprint of the API key, so rows
    never cross keys. Rows orphaned by a rotation stay unread in the same file:
    rows on a finite TTL age out, while match and timeline rows never expire
    and remain until ``clear_cache()``, which clears the file for every key.
    """

    key_namespace: str
    """Fingerprint prefix on every cache key, assigned by ``create_cache_backend``."""

    def create_key(self, method: str, url: StrOrURL, **kwargs: object) -> str:
        """The library's cache key, prefixed with the API key fingerprint."""
        return f"{self.key_namespace}:{super().create_key(method, url, **kwargs)}"


_AUTH_HEADER_NAME = "X-Riot-Token"


class _TokenStrippedResponse:
    """Read-through response proxy whose request headers carry no credential.

    Every nexar request sends the API key as ``X-Riot-Token``, and since
    aiohttp-client-cache 0.14 the stored row copies ``request_info.headers``
    into ``request_raw_headers``, so the key would persist in plaintext in
    the sqlite file for as long as the row lives. A live response's
    ``request_info`` is a read-only cached property, so the token cannot be
    removed in place: this proxy rebuilds the named tuple without the
    header, and the library's row conversion reads the cleaned copy. On
    library versions that store no request headers the proxy is a
    pass-through with no effect.
    """

    def __init__(self, response: ClientResponse) -> None:
        self._response = response

    def __getattr__(self, name: str) -> object:
        return getattr(self._response, name)

    @property
    def request_info(self) -> RequestInfo:
        """The response's request_info with the token header removed."""
        info = self._response.request_info
        if _AUTH_HEADER_NAME not in info.headers:
            return info
        token = _AUTH_HEADER_NAME.lower()
        cleaned = CIMultiDict(header for header in info.headers.items() if header[0].lower() != token)
        return RequestInfo(url=info.url, method=info.method, headers=CIMultiDictProxy(cleaned), real_url=info.real_url)

    @property
    def history(self) -> tuple[ClientResponse, ...]:
        """Redirect members wrapped the same way, so their rows stay clean too.

        The library recurses into history when it stores a response, so an
        unwrapped member would carry the token into the row even with the
        top-level headers stripped. Riot does not redirect today; this keeps
        the guarantee true on the day it does.
        """
        return tuple(
            cast("ClientResponse", _TokenStrippedResponse(redirected)) for redirected in self._response.history
        )


class NexarSQLiteBackend(SQLiteBackend, _KeyNamespacedBackend):
    """SQLite backend that never caches cookies or the auth token, and drops rows it cannot load.

    Riot's API responses carry a Cloudflare ``__cf_bm`` Set-Cookie whose ``Partitioned``
    attribute ``http.cookies`` rejects when a cached row is unpickled. aiohttp-client-cache
    pickles the whole response, cookies included, and its deserialize guard does not catch
    ``CookieError``, so a single cached cookie made every later read of that row crash.
    Cookies are anti-bot session noise, not API data: they are stripped before the row is
    written, and a row written by an older version that still fails to load is deleted and
    treated as a cache miss, so a poisoned cache heals itself on the next fetch.
    """

    async def save_response(
        self,
        response: ClientResponse,
        cache_key: str | None = None,
        expires: datetime | None = None,
    ) -> None:
        """Save a response with its cookie jar emptied and its credential stripped.

        The jar on the live response is a parsed copy nobody consumes; the session's
        cookie jar was already updated when the response arrived, so nothing is lost.
        The token proxy keeps the API key out of the stored row: newer
        aiohttp-client-cache copies request headers into the row it writes.
        """
        response.cookies.clear()
        for redirected in response.history:
            redirected.cookies.clear()
        # The library declares ClientResponse but reads it structurally; the
        # proxy answers every attribute it reads, with a clean request_info.
        stripped = cast("ClientResponse", _TokenStrippedResponse(response))
        await super().save_response(stripped, cache_key, expires)

    async def get_response(self, key: str) -> CachedResponse | None:
        """Read a cached response, treating an unreadable row as a cache miss."""
        try:
            return await super().get_response(key)
        except (CookieError, pickle.UnpicklingError, EOFError, sqlite3.Error):
            logger.warning("Dropping cached row %s: it cannot be loaded. Refetching.", key)
            # kv-level delete: CacheBackend.delete() deserializes the row first,
            # which would raise again.
            await self.responses.delete(key)
            return None


def create_cache_backend(config: CacheConfig, api_key: str) -> CacheBackend:
    """Create an aiohttp-client-cache backend based on the provided configuration.

    Rows are namespaced by a fingerprint of ``api_key`` (hashed, never the
    key itself), so two keys sharing one sqlite file never read each other's
    cached responses.
    """
    key_namespace = _api_key_fingerprint(api_key)
    if config.backend == "sqlite":
        cache_dir = Path(config.cache_dir) if config.cache_dir else (Path.home() / ".nexar")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{config.cache_name}.sqlite"
        backend = NexarSQLiteBackend(
            cache_name=str(cache_path.with_suffix("")),
            expire_after=config.expire_after,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            allowed_codes=(200,),
        )
        backend.key_namespace = key_namespace
        return backend

    if config.backend == "memory":
        # A CacheBackend subclass with its default in-memory DictCache storage
        # (namespaced like the sqlite backend, though a memory backend is
        # private to its client anyway). Passing a bare DictCache here does not
        # work: it is a storage, not a backend, and CachedSession silently
        # swaps out a falsy cache for a default one, dropping the TTL wiring.
        backend = _KeyNamespacedBackend(
            expire_after=config.expire_after,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            allowed_codes=(200,),
        )
        backend.key_namespace = key_namespace
        return backend

    msg = f"Unsupported cache backend: {config.backend}"
    raise ValueError(msg)


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for API response caching."""

    enabled: bool = True
    """Whether caching is enabled."""

    cache_name: str = "nexar_cache"
    """Name of the cache file (without extension)."""

    backend: Literal["sqlite", "memory"] = "sqlite"
    """Cache backend to use ('sqlite' for persistence, 'memory' for ephemeral)."""

    cache_dir: str | Path | None = None
    """Directory path for cache storage (defaults to ~/.nexar/)."""

    expire_after: int | None = ttl(hours=1)
    """Default expiration time in seconds for endpoints not covered by smart TTLs."""

    timeout: int = 30
    """HTTP request timeout in seconds."""


DEFAULT_CACHE_CONFIG = CacheConfig()
"""Default cache: SQLite, 1-hour default TTL, plus smart endpoint TTLs."""

NO_CACHE_CONFIG = CacheConfig(enabled=False)
"""Configuration that disables caching entirely."""
