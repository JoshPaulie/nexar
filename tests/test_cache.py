"""Cached rows never persist the wire credential.

Every nexar request sends the API key as ``X-Riot-Token``, and newer
aiohttp-client-cache releases copy request headers into the stored row, so a
live call wrote the key in plaintext into the sqlite cache file. The proxy
rows pin the seam on the locked library version; the bytes row is the
tripwire for a lock bump, and on a fresh install, which resolves the newer
library today, it is the defect itself, measured 2026-11-22.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest_asyncio
from aiohttp import ClientResponse, RequestInfo
from aiohttp_client_cache.backends.base import CacheBackend
from aioresponses.core import RequestMatch
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from nexar.cache import CacheConfig, _TokenStrippedResponse, create_cache_backend

FAKE_API_KEY = "RGAPI-cache-row-0123456789abcdef"

ROW_URL = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/bexli/bex"
ROW_PAYLOAD = {"puuid": "puuid-x", "gameName": "bexli", "tagLine": "bex"}


def _armed_response() -> ClientResponse:
    """A response carrying the token on request_info, as live traffic does.

    aioresponses has no public way to arm a fabricated response's
    request_info, and a live ClientResponse makes it a read-only cached
    property, so the arming goes through RequestMatch directly.
    """
    return RequestMatch(ROW_URL)._build_response(
        URL(ROW_URL), method="GET", request_headers={"X-Riot-Token": FAKE_API_KEY}, payload=ROW_PAYLOAD
    )


@pytest_asyncio.fixture
async def row_backend(tmp_path: Path) -> AsyncGenerator[CacheBackend]:
    """A sqlite cache backend whose file lives and dies in tmp_path."""
    backend = create_cache_backend(
        CacheConfig(backend="sqlite", cache_dir=str(tmp_path), cache_name="rowcheck"), FAKE_API_KEY
    )
    yield backend
    await backend.close()


async def test_token_strip_proxy_removes_the_riot_token() -> None:
    response = _armed_response()
    assert response.request_info.headers["X-Riot-Token"] == FAKE_API_KEY

    stripped = _TokenStrippedResponse(response)

    assert "X-Riot-Token" not in stripped.request_info.headers
    assert isinstance(stripped.request_info.headers, CIMultiDictProxy)
    assert isinstance(response.request_info, RequestInfo)
    # Identity fields survive the rebuild.
    assert stripped.request_info.real_url == response.request_info.real_url
    assert stripped.method == "GET"
    assert stripped.status == 200


async def test_token_strip_proxy_passes_clean_responses_through() -> None:
    response = RequestMatch(ROW_URL)._build_response(URL(ROW_URL), method="GET", payload=ROW_PAYLOAD)
    assert "X-Riot-Token" not in response.request_info.headers

    proxy = _TokenStrippedResponse(response)

    assert proxy.request_info is response.request_info


async def test_saved_row_carries_no_riot_token(
    row_backend: CacheBackend,
    tmp_path: Path,
) -> None:
    # Tables exist only after the first awaited call.
    assert await row_backend.get_response("warmup") is None
    response = _armed_response()

    await row_backend.save_response(response, cache_key="cache-row")

    raw = (tmp_path / "rowcheck.sqlite").read_bytes()
    # A row that never wrote would pass the token check vacuously.
    assert b"bexli" in raw
    # The locked library stores no request headers, so this is the tripwire
    # for a lock bump; a fresh install resolves a version that does store
    # them, and there the strip above keeps this assertion true.
    assert FAKE_API_KEY.encode() not in raw

    replay = await row_backend.get_response("cache-row")
    assert replay is not None
    assert replay.status == 200
    assert "X-Riot-Token" not in replay.request_info.headers
