"""Unit tests for the RateLimiter class."""

import time

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_acquire_under_limit() -> None:
    limiter = MockRateLimiter(((2, 1), (10, 60)), safety_margin=0)
    await limiter.acquire("na1", "summoner-v4")
    app_key = "app_na1_2:1"
    assert limiter.limits["na1"][app_key].count == 1

    await limiter.acquire("na1", "summoner-v4")
    assert limiter.limits["na1"][app_key].count == 2


@pytest.mark.asyncio
async def test_acquire_over_limit_with_sleep(mocker) -> None:
    limiter = MockRateLimiter(((1, 10), (100, 600)), safety_margin=0)

    mock_sleep = mocker.patch("asyncio.sleep", return_value=None)
    current_time = [time.time()]

    def get_time():
        return current_time[0]

    mocker.patch("time.time", side_effect=get_time)

    await limiter.acquire("na1", "summoner-v4")
    current_time[0] += 1

    async def mock_sleep_adv(sec) -> None:
        current_time[0] += sec + 1

    mock_sleep.side_effect = mock_sleep_adv
    await limiter.acquire("na1", "summoner-v4")

    assert mock_sleep.call_count == 1
    assert limiter.limits["na1"]["app_na1_1:10"].count == 1  # Reset after sleep


@pytest.mark.asyncio
async def test_update_from_headers() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-App-Rate-Limit": "20:1,100:120",
        "X-App-Rate-Limit-Count": "5:1,10:120",
        "X-Method-Rate-Limit": "100:10",
        "X-Method-Rate-Limit-Count": "1:10",
    }

    await limiter.update_from_headers(headers, "na1", "summoner-v4")

    assert "app_na1_20:1" in limiter.limits["na1"]
    assert limiter.limits["na1"]["app_na1_20:1"].count == 5
    assert limiter.limits["na1"]["method_na1_summoner-v4_100:10"].count == 1


@pytest.mark.asyncio
async def test_update_from_headers_service() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-Service-Rate-Limit": "500:60",
        "X-Service-Rate-Limit-Count": "200:60",
    }

    await limiter.update_from_headers(headers, "na1", "summoner-v4")

    assert "service_na1_500:60" in limiter.limits["na1"]
    assert limiter.limits["na1"]["service_na1_500:60"].count == 200
