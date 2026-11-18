"""Behavior tests for the sliding-window RateLimiter."""

import asyncio
import time

import pytest

from nexar.rate_limiter import PERSONAL_LIMITS, RateLimiter


def _assert_windows_hold(admissions: list[float], limits: tuple[tuple[int, int], ...]) -> None:
    """No sliding window may ever contain more than its limit."""
    for limit, window in limits:
        for i, t in enumerate(admissions):
            n = sum(1 for s in admissions if t <= s < t + window)
            assert n <= limit, f"{n} admissions in a {window}s window (limit {limit}) at t={t:.3f}"


@pytest.mark.asyncio
async def test_full_burst_admitted_immediately() -> None:
    """12 requests (under the 20/1s limit) all admit instantly."""
    limiter = RateLimiter(PERSONAL_LIMITS)
    t0 = time.monotonic()
    await asyncio.gather(*(limiter.acquire("na1") for _ in range(12)))
    elapsed = time.monotonic() - t0

    assert len(limiter._admitted["na1"]) == 12
    assert elapsed < 2.0, f"burst throttled below the documented limit: {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_windows_never_exceeded_under_load() -> None:
    """Under saturating concurrent load, every window holds at or under its limit."""
    limits = ((5, 1), (10, 2))
    limiter = RateLimiter(limits)
    t0 = time.monotonic()

    async def timed() -> float:
        await limiter.acquire("na1")
        return time.monotonic()

    times = await asyncio.gather(*(timed() for _ in range(12)))
    admissions = sorted(t - t0 for t in times)

    _assert_windows_hold(admissions, limits)
    # 12 admissions against a 5-per-1s window: at least one had to wait
    assert admissions[-1] > 0.9


@pytest.mark.asyncio
async def test_long_window_gates_burst() -> None:
    """The long window paces admissions once its capacity is full."""
    limits = ((2, 1), (6, 2))
    limiter = RateLimiter(limits)
    t0 = time.monotonic()

    async def timed() -> float:
        await limiter.acquire("na1")
        return time.monotonic()

    times = await asyncio.gather(*(timed() for _ in range(8)))
    elapsed = time.monotonic() - t0
    admissions = sorted(t - t0 for t in times)

    _assert_windows_hold(admissions, limits)
    # 6 fit in the first 2s window; the last 2 must wait for the oldest to exit
    assert admissions[-1] >= 1.5, f"long window did not gate the burst: {elapsed:.2f}s"
    assert elapsed < 5


@pytest.mark.asyncio
async def test_block_waits_then_clears() -> None:
    """A 429 Retry-After block halts admissions for roughly the blocked duration."""
    limiter = RateLimiter()
    await limiter.acquire("na1")
    limiter.block("na1", 0.25)

    t0 = time.monotonic()
    await limiter.acquire("na1")
    waited = time.monotonic() - t0
    assert 0.2 <= waited <= 0.6, f"expected ~0.25s block, waited {waited:.2f}s"

    # After the block expires, admissions resume instantly
    t0 = time.monotonic()
    await limiter.acquire("na1")
    assert time.monotonic() - t0 < 0.1


@pytest.mark.asyncio
async def test_regions_pace_independently() -> None:
    """Saturating one region must not slow another."""
    limiter = RateLimiter(((2, 1), (4, 2)))
    t0 = time.monotonic()
    await asyncio.gather(*(limiter.acquire("na1") for _ in range(6)))
    na1_elapsed = time.monotonic() - t0
    # both na1 windows were saturated, so admissions had to pace
    assert na1_elapsed >= 1.5, f"na1 never saturated: {na1_elapsed:.2f}s"

    t0 = time.monotonic()
    await limiter.acquire("br1")
    assert time.monotonic() - t0 < 0.05, "br1 must admit instantly while na1 is saturated"


@pytest.mark.asyncio
async def test_block_does_not_leak_across_regions() -> None:
    """A 429 block on one region must not block another."""
    limiter = RateLimiter()
    limiter.block("na1", 0.3)

    t0 = time.monotonic()
    await limiter.acquire("br1")
    assert time.monotonic() - t0 < 0.05


@pytest.mark.asyncio
async def test_seed_from_counts_admits_only_remaining_slots() -> None:
    """A fresh client oriented from server counts admits exactly the remainder.

    Regression for the cold-start hole: without the seed, a restarted client
    assumes empty windows and re-bursts into a partially spent quota.
    """
    limits = ((5, 1), (10, 3))
    limiter = RateLimiter(limits)

    await limiter.acquire("na1")  # the "current call", counted by the server
    limiter.seed_from_counts("na1", {1: 1, 3: 6})

    # The 5 counted calls land in the older band (outside the 1s window), so
    # the 1s window is not poisoned by the seed and the 4 remaining long-window
    # slots (10 - 6) admit instantly. This is the regression check: a per-window
    # seed would put all 5 inside the 1s window and block for a full second.
    t0 = time.monotonic()
    await asyncio.gather(*(limiter.acquire("na1") for _ in range(4)))
    elapsed = time.monotonic() - t0
    assert elapsed < 0.5, f"short window was poisoned by the seed: {elapsed:.2f}s"

    # both windows are now full (5/5 in 1s, 10/10 in 3s): the next acquire
    # must wait for the seeded band to age out, not admit
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(limiter.acquire("na1"), timeout=0.5)


@pytest.mark.asyncio
async def test_seed_inner_band_holds_short_window() -> None:
    """Calls counted inside the shortest window must hold its slots."""
    limits = ((5, 1), (10, 3))
    limiter = RateLimiter(limits)

    await limiter.acquire("na1")
    limiter.seed_from_counts("na1", {1: 5, 3: 10})

    # 5/5 in the 1s window (current + 4 seeded at now): the next acquire
    # must wait ~1s for the inner band to age out, not admit
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(limiter.acquire("na1"), timeout=0.5)


@pytest.mark.asyncio
async def test_seed_is_idempotent_and_region_scoped() -> None:
    limiter = RateLimiter(((5, 1), (10, 3)))
    await limiter.acquire("na1")
    limiter.seed_from_counts("na1", {1: 1, 3: 6})
    before = len(limiter._admitted["na1"])

    # A second seed (later response) must be a no-op
    limiter.seed_from_counts("na1", {1: 99, 3: 99})
    assert len(limiter._admitted["na1"]) == before

    # Seeding na1 must not touch br1
    t0 = time.monotonic()
    await limiter.acquire("br1")
    assert time.monotonic() - t0 < 0.05
