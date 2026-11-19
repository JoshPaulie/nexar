"""Unit tests for cache configuration."""

import pickle
import sqlite3
from http.cookies import Morsel, SimpleCookie
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from aiohttp_client_cache.backends import DictCache  # type: ignore[attr-defined]
from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from aiohttp_client_cache.session import CachedSession

from nexar.cache import (
    DEFAULT_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    CacheConfig,
    create_cache_backend,
)

if TYPE_CHECKING:
    from aioresponses import aioresponses


def _poisoned_cookie() -> SimpleCookie:
    """Recreate the poisoned morsel found in real cache rows on 2026-11-18.

    Riot's Cloudflare ``__cf_bm`` Set-Cookie carries a ``Partitioned`` attribute that
    ``http.cookies`` refuses to validate; the attribute rides along into the pickled
    cache row and detonates on every later unpickle.
    """
    morsel = Morsel()
    morsel.set("__cf_bm", "abc", "abc")
    dict.__setitem__(morsel, "partitioned", "yes")
    cookie = SimpleCookie()
    dict.__setitem__(cookie, "__cf_bm", morsel)
    return cookie


class TestCreateCacheBackend:
    def test_sqlite_backend(self, tmp_path: Path) -> None:
        config = CacheConfig(backend="sqlite", cache_name="test", cache_dir=str(tmp_path))
        backend = create_cache_backend(config)
        assert isinstance(backend, SQLiteBackend)
        assert backend.expire_after == 3600

    def test_memory_backend(self) -> None:
        config = CacheConfig(backend="memory")
        backend = create_cache_backend(config)
        assert isinstance(backend, DictCache)

    def test_invalid_backend_raises(self) -> None:
        config = CacheConfig(backend="invalid")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported cache backend"):
            create_cache_backend(config)


class TestCacheConfigDefaults:
    def test_default_config_is_enabled(self) -> None:
        assert DEFAULT_CACHE_CONFIG.enabled is True

    def test_no_cache_config_is_disabled(self) -> None:
        assert NO_CACHE_CONFIG.enabled is False


class TestSQLiteCookieHygiene:
    """Cached cookies poison sqlite rows: never store them, heal rows that have them."""

    async def test_unreadable_row_is_a_miss_and_is_deleted(self, tmp_path: Path) -> None:
        """A row written by an older version reads as a cache miss and is dropped."""
        backend = create_cache_backend(CacheConfig(cache_name="test", cache_dir=str(tmp_path)))
        db_path = tmp_path / "test.sqlite"

        assert await backend.get_response("warmup") is None  # forces sqlite schema creation

        poison = pickle.dumps(_poisoned_cookie())
        with sqlite3.connect(db_path) as db:
            db.execute("INSERT INTO responses (key, value) VALUES (?, ?)", ("deadrow", poison))

        assert await backend.get_response("deadrow") is None

        with sqlite3.connect(db_path) as db:
            (count,) = db.execute("SELECT COUNT(*) FROM responses WHERE key = ?", ("deadrow",)).fetchone()
        assert count == 0
        await backend.close()

    async def test_saved_rows_carry_no_cookies_and_reread_cleanly(
        self,
        tmp_path: Path,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """A response carrying the live poisoned cookie saves clean and reloads without crashing."""
        url = "https://na1.api.riotgames.com/lol/test/cookie"
        mock_aioresponse.get(url, headers={"Set-Cookie": "__cf_bm=abc; Partitioned"}, payload={"ok": True})

        backend = create_cache_backend(CacheConfig(cache_name="test", cache_dir=str(tmp_path)))
        async with CachedSession(cache=backend) as session:
            response = await session.get(url)
            assert "set-cookie" in response.headers
            # aioresponses fabricates a lowercase method; the live stack sends
            # uppercase, which is what the cache's allowed_methods accepts.
            response.method = "GET"
            # Reproduce the state the live stack lands in: a morsel carrying an
            # attribute http.cookies rejects sits in the response's cookie jar.
            response.cookies = _poisoned_cookie()
            await backend.save_response(response)
        await backend.close()

        db_path = tmp_path / "test.sqlite"
        with sqlite3.connect(db_path) as db:
            (blob,) = db.execute("SELECT value FROM responses LIMIT 1").fetchone()
        stored = pickle.loads(blob)  # noqa: S301 - fixture data this test wrote itself
        assert not stored.cookies

        backend2 = create_cache_backend(CacheConfig(cache_name="test", cache_dir=str(tmp_path)))
        replayed = await backend2.get_response(backend2.create_key("GET", url))
        await backend2.close()
        assert replayed is not None
        assert not replayed.cookies
