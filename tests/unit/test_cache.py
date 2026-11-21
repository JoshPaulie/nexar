"""Unit tests for cache configuration."""

import pickle
import sqlite3
from http.cookies import Morsel, SimpleCookie
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import aiohttp
import pytest
from aiohttp_client_cache.backends import CacheBackend
from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from aiohttp_client_cache.cache_control import CacheActions, ExpirationTime
from aiohttp_client_cache.session import CachedSession

from nexar.cache import (
    _SMART_ENDPOINT_TTLS,
    DEFAULT_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    CacheConfig,
    create_cache_backend,
    ttl,
)
from nexar.client import NexarClient
from nexar.enums import Region

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


class TestSmartEndpointTtls:
    def test_immutable_match_rows_never_expire(self) -> None:
        """The match-v5 glob must resolve to the library's never-expire sentinel.

        ``CacheActions`` coalesces per-URL over per-session expiration, skipping
        ``None`` values — so a ``None`` pattern row is indistinguishable from no
        match and quietly resolves to the 1-hour session default. Resolved
        through ``CacheActions.from_settings`` (the library's own resolution
        path), not the raw dict value: the claim under test is the effective
        expiry of the URL, which the dict alone cannot prove.
        """
        for url in (
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_5671503499/timeline",
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_5671503499",
        ):
            actions = CacheActions.from_settings(
                key="probe",
                url=url,
                urls_expire_after=_SMART_ENDPOINT_TTLS,
                session_expire_after=DEFAULT_CACHE_CONFIG.expire_after,
            )
            assert actions.expire_after == -1
            assert actions.expires is None

    def test_freshness_rows_keep_their_ttl(self) -> None:
        """The specificity-ordered rows still resolve ahead of the session default."""
        actions = CacheActions.from_settings(
            key="probe",
            url="https://na1.api.riotgames.com/lol/champion-mastery/v4/scores/by-puuid/p",
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            session_expire_after=DEFAULT_CACHE_CONFIG.expire_after,
        )
        assert actions.expire_after == 30 * 60

    @pytest.mark.parametrize(
        ("url", "expected_expire_after"),
        [
            ("https://na1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5", 5 * 60),
            ("https://na1.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5", 5 * 60),
            ("https://na1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5", 5 * 60),
            ("https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/I", 5 * 60),
            ("https://na1.api.riotgames.com/lol/league-exp/v4/entries/RANKED_SOLO_5x5/GOLD/I", 5 * 60),
            ("https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/p", 5 * 60),
            ("https://na1.api.riotgames.com/lol/platform/v3/champion-rotations", 24 * 60 * 60),
            ("https://na1.api.riotgames.com/lol/status/v4/platform-data", 60),
        ],
        ids=[
            "challenger",
            "grandmaster",
            "master",
            "division-entries",
            "league-exp-entries",
            "by-puuid-entries",
            "rotations",
            "status",
        ],
    )
    def test_ladder_rotation_status_rows_keep_their_freshness_class(
        self,
        url: str,
        expected_expire_after: int,
    ) -> None:
        """Ladder rows ride the 5-minute league class, rotations the day class, status minutes.

        Resolved through CacheActions.from_settings (the library's own
        resolution path), not the raw dict value: the claim under test is the
        effective expiry of each URL. The page query parameter is not part of
        the URL pattern matching, so the division rows cover every page of
        those ladders.
        """
        actions = CacheActions.from_settings(
            key="probe",
            url=url,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            session_expire_after=DEFAULT_CACHE_CONFIG.expire_after,
        )
        assert actions.expire_after == expected_expire_after

    def test_division_glob_cannot_shadow_the_by_puuid_row(self) -> None:
        """The structural no-shadow proof — against the division glob ALONE, a by-puuid URL falls through.

        Both rows carry the same 5-minute TTL, so resolving a by-puuid URL
        against the full dict cannot tell which row answered. Against a
        division-only subset, the by-puuid URL resolving to the session
        default is the observable difference between "matched no row" and
        "matched the wrong row". The mechanism: the glob requires two literal
        slashes after /entries/ and by-puuid URLs carry one (fnmatch ``*``
        crosses slashes, but the pattern's own slashes are literal).
        """
        division_only: dict[str, ExpirationTime] = {"*/lol/league/v4/entries/*/*/*": ttl(minutes=5)}
        actions = CacheActions.from_settings(
            key="probe",
            url="https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/p",
            urls_expire_after=division_only,
            session_expire_after=DEFAULT_CACHE_CONFIG.expire_after,
        )
        assert actions.expire_after == DEFAULT_CACHE_CONFIG.expire_after


class TestCreateCacheBackend:
    @pytest.mark.parametrize("backend_name", ["sqlite", "memory"])
    def test_backend_wiring(self, tmp_path: Path, backend_name: Literal["sqlite", "memory"]) -> None:
        """Both backends carry the smart endpoint TTLs (preceding the default) and cache 200s only."""
        config = CacheConfig(
            backend=backend_name,
            cache_name="test",
            cache_dir=str(tmp_path),
            expire_after=60,
        )
        backend = create_cache_backend(config)

        assert isinstance(backend, CacheBackend)
        if backend_name == "sqlite":
            assert isinstance(backend, SQLiteBackend)  # the cookie-hardened subclass
        assert backend.expire_after == 60
        assert backend.urls_expire_after is not None
        # Per-endpoint TTLs take precedence over the 60s default expire_after.
        # -1 is the library's never-expire sentinel (None is skipped by coalesce).
        assert backend.urls_expire_after["*/lol/match/v5/matches/*"] == -1  # immutable: cached forever
        assert backend.urls_expire_after["*/lol/league/v4/entries/by-puuid/*"] == 300  # 5 minutes
        assert (
            backend.urls_expire_after["*/lol/champion-mastery/v4/champion-masteries/by-puuid/*"] == 1800
        )  # 30 minutes
        assert backend.urls_expire_after["*/riot/account/v1/accounts/by-riot-id/*"] == 86400  # 1 day
        assert backend.allowed_codes == (200,)

    def test_invalid_backend_raises(self) -> None:
        config = CacheConfig(backend="invalid")  # ty: ignore[invalid-argument-type]
        with pytest.raises(ValueError, match="Unsupported cache backend"):
            create_cache_backend(config)


class TestCacheSessionWiring:
    @pytest.mark.parametrize(
        ("config", "expected_type"),
        [
            (DEFAULT_CACHE_CONFIG, CachedSession),
            (NO_CACHE_CONFIG, aiohttp.ClientSession),
        ],
        ids=["default-caches", "no-cache-plain-session"],
    )
    async def test_config_wires_session_type(self, config: CacheConfig, expected_type: type) -> None:
        """The two shipped configs build the documented session types."""
        client = NexarClient(riot_api_key="key", default_region=Region.NA1, cache_config=config)
        await client._ensure_session()
        try:
            assert isinstance(client._session, expected_type)
        finally:
            await client.close()


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
