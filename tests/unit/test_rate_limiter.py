"""Unit tests for the RateLimiter class backed by aiolimiter."""

import time

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_acquire_under_limit() -> None:
    """Acquiring within the limit should not block and should consume capacity."""
    limiter = MockRateLimiter(((2, 1), (10, 60)), safety_margin=0)

    await limiter.acquire("na1", "summoner-v4")
    # After 1 acquire on a 2/1s bucket, there should still be capacity
    buckets = limiter.app_buckets["na1"]
    assert buckets[0].has_capacity()  # 1/2 used

    await limiter.acquire("na1", "summoner-v4")
    # After 2 acquires on a 2/1s bucket, capacity exhausted
    assert not buckets[0].has_capacity()  # 2/2 used


@pytest.mark.asyncio
async def test_acquire_over_limit_with_sleep(mocker) -> None:
    """Acquiring over the limit should sleep until capacity is available."""
    limiter = MockRateLimiter(((1, 10), (100, 600)), safety_margin=0)

    mock_sleep = mocker.patch("asyncio.sleep", return_value=None)
    current_time = [time.time()]

    def get_time():
        return current_time[0]

    mocker.patch("time.time", side_effect=get_time)

    await limiter.acquire("na1", "summoner-v4")

    async def mock_sleep_adv(sec) -> None:
        current_time[0] += sec + 1

    mock_sleep.side_effect = mock_sleep_adv
    await limiter.acquire("na1", "summoner-v4")

    # Should have slept because bucket was full
    assert mock_sleep.call_count >= 1


@pytest.mark.asyncio
async def test_update_from_headers() -> None:
    """Method rate limits from headers should create dynamic AsyncLimiter instances."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-App-Rate-Limit": "20:1,100:120",
        "X-App-Rate-Limit-Count": "5:1,10:120",
        "X-Method-Rate-Limit": "100:10",
        "X-Method-Rate-Limit-Count": "1:10",
    }

    await limiter.update_from_headers(headers, "na1", "summoner-v4")

    # Method limit buckets should exist in dynamic
    method_key = "method_na1_summoner-v4_100:10"
    assert method_key in limiter.dynamic
    assert limiter.dynamic[method_key].max_rate == 99  # 100 * 0.99 safety margin


@pytest.mark.asyncio
async def test_update_from_headers_service() -> None:
    """Service rate limits from headers should create dynamic AsyncLimiter instances."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-Service-Rate-Limit": "500:60",
        "X-Service-Rate-Limit-Count": "200:60",
    }

    await limiter.update_from_headers(headers, "na1", "summoner-v4")

    # Service limit bucket should exist in dynamic
    service_key = "service_na1_500:60"
    assert service_key in limiter.dynamic
    assert limiter.dynamic[service_key].max_rate == 495  # 500 * 0.99 safety margin
