"""Unit tests for the RateLimiter class backed by aiolimiter."""

import time

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_acquire_under_limit() -> None:
    """Acquiring within the limit should not block and should consume capacity.

    App-level buckets use burst=1 to conservatively match Riot's sliding-window
    enforcement. A single acquire drains the bucket; further acquires wait for refill.
    """
    limiter = MockRateLimiter(((2, 1), (10, 60)))

    await limiter.acquire("na1", "summoner-v4")
    # Burst=1 bucket: capacity is exhausted after 1 acquire
    buckets = limiter.app_buckets["na1"]
    assert not buckets[0].has_capacity()  # burst=1 fully consumed

    # Second acquire: bucket is empty, must wait for refill then acquire
    await limiter.acquire("na1", "summoner-v4")
    assert not buckets[0].has_capacity()  # burst=1 consumed again


@pytest.mark.asyncio
async def test_acquire_over_limit_with_sleep(mocker) -> None:
    """Acquiring over the limit should sleep until capacity is available.

    With burst=1 and limit=1 per 10s, the bucket refills after ~10s.
    """
    limiter = MockRateLimiter(((1, 10), (100, 600)))

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
    assert limiter.dynamic[method_key].max_rate == 100


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
    assert limiter.dynamic[service_key].max_rate == 500


# -- _compute_burst_period ---------------------------------------------------


def test_compute_burst_period_limit_20_per_1s() -> None:
    """20 req / 1s should produce period ~0.0526s."""
    from nexar.rate_limiter import RateLimiter

    period = RateLimiter._compute_burst_period(20, 1)
    # period = 1 / (20 - 1) = 1/19 ≈ 0.05263
    assert period == pytest.approx(1 / 19)


def test_compute_burst_period_limit_100_per_120s() -> None:
    """100 req / 120s should produce period ~1.212s."""
    from nexar.rate_limiter import RateLimiter

    period = RateLimiter._compute_burst_period(100, 120)
    # period = 120 / (100 - 1) = 120/99 ≈ 1.21212
    assert period == pytest.approx(120 / 99)


def test_compute_burst_period_limit_1() -> None:
    """Limit=1: burst consumes entire quota, so period = window."""
    from nexar.rate_limiter import RateLimiter

    period = RateLimiter._compute_burst_period(1, 10)
    assert period == 10


# -- _refill_wait -------------------------------------------------------------


@pytest.mark.asyncio
async def test_refill_wait_all_capacity_available() -> None:
    """When all buckets have capacity, _refill_wait returns the floor of 0.1s."""
    from aiolimiter import AsyncLimiter

    from nexar.rate_limiter import RateLimiter

    # Fresh burst=1 buckets — all have capacity
    buckets = [AsyncLimiter(1, 10), AsyncLimiter(1, 120)]
    wait = RateLimiter._refill_wait(buckets)
    assert wait == 0.1


@pytest.mark.asyncio
async def test_refill_wait_one_empty() -> None:
    """One empty burst=1 bucket: wait is 15% of its refill period."""
    from aiolimiter import AsyncLimiter

    from nexar.rate_limiter import RateLimiter

    bucket = AsyncLimiter(1, 10)  # burst=1, refills one token per 10s
    await bucket.acquire()  # drain the token

    wait = RateLimiter._refill_wait([bucket])
    # refill time = time_period / max_rate = 10 / 1 = 10s, * 0.15 = 1.5
    assert wait == 1.5


@pytest.mark.asyncio
async def test_refill_wait_mixed_empty_and_full() -> None:
    """Wait is determined by the slowest-to-refill empty bucket."""
    from aiolimiter import AsyncLimiter

    from nexar.rate_limiter import RateLimiter

    slow = AsyncLimiter(1, 100)  # refill: 100s per token
    fast = AsyncLimiter(1, 10)   # refill: 10s per token
    await slow.acquire()
    await fast.acquire()

    full = AsyncLimiter(1, 50)  # still has capacity

    wait = RateLimiter._refill_wait([slow, fast, full])
    # slow dominates: 100s * 0.15 = 15s
    assert wait == 15.0


@pytest.mark.asyncio
async def test_refill_wait_with_dynamic_large_burst_bucket() -> None:
    """Dynamic buckets have larger burst; refill time is time_period / max_rate."""
    from aiolimiter import AsyncLimiter

    from nexar.rate_limiter import RateLimiter

    # Simulate a dynamic bucket: burst=100, window=10s, rate=10/s
    bucket = AsyncLimiter(100, 10)
    await bucket.acquire()  # drain one token, bucket still has capacity

    # Bucket still has capacity (99 left), so no wait
    wait = RateLimiter._refill_wait([bucket])
    assert wait == 0.1


@pytest.mark.asyncio
async def test_refill_wait_dynamic_bucket_fully_drained() -> None:
    """Fully drained dynamic bucket: wait is 15% of (window / max_rate)."""
    from aiolimiter import AsyncLimiter

    from nexar.rate_limiter import RateLimiter

    # Dynamic bucket: burst=500, window=10s
    bucket = AsyncLimiter(500, 10)
    for _ in range(500):
        await bucket.acquire()
    assert not bucket.has_capacity()

    # refill time = 10 / 500 = 0.02s per token, * 0.15 = 0.003
    wait = RateLimiter._refill_wait([bucket])
    assert wait == pytest.approx(0.02 * 0.15)
