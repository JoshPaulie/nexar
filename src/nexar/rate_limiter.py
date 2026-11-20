"""Rate limiting for the Riot API via a sliding-window log.

Riot enforces each application rate window (e.g. 20 per 1s, 100 per 120s)
as a sliding window, per region, per API key. This limiter mirrors that
rule directly: it records the monotonic time of every admitted request and
admits the next one only when every window has a free slot. For a single
process using one key this is exactly the rule the server applies, so the
full documented quota is usable (20 requests may fire in the first
second) while no window is ever exceeded.

On a 429 the client blocks the region for the Retry-After duration —
Riot's documented remedy. Method and service rate limits are deliberately
not tracked: the application window always binds first at every key tier
(personal: 100/120s app vs. method limits like 2000/10s; production:
50/s app vs. 200/s method), so tracking them cannot change behavior.
"""

import asyncio
import logging
import time
from collections import deque

logger = logging.getLogger("nexar")

# Standard Riot API rate limits: https://developer.riotgames.com/docs/portal
PERSONAL_LIMITS: tuple[tuple[int, int], ...] = ((20, 1), (100, 120))
PRODUCTION_LIMITS: tuple[tuple[int, int], ...] = ((500, 10), (30000, 600))


def _validate_rate_limit(limit: int, window: int) -> None:
    """Validate that rate limit values are positive and within reasonable bounds."""
    if limit <= 0:
        msg = f"Rate limit must be positive, got {limit}"
        raise ValueError(msg)
    if window <= 0:
        msg = f"Window must be positive, got {window} seconds"
        raise ValueError(msg)
    if limit > 1_000_000:
        msg = f"Rate limit suspiciously high: {limit}"
        raise ValueError(msg)
    if window > 86400:
        msg = f"Window suspiciously long: {window} seconds (>24h)"
        raise ValueError(msg)


class RateLimiter:
    """Sliding-window admission per region, plus Retry-After blocking.

    The check-and-claim block is synchronous (no ``await`` between reading
    and appending the admission timestamp), which makes it atomic on a
    single event loop — no locks are needed. The only ``await`` is the
    final sleep, held while nothing is locked, so concurrent callers never
    starve each other's progress.
    """

    def __init__(
        self,
        app_limits: tuple[tuple[int, int], ...] = PERSONAL_LIMITS,
    ) -> None:
        """Initialize with application-level limits as (count, window_seconds) tuples."""
        for limit, window in app_limits:
            _validate_rate_limit(limit, window)
        self._app_limits = app_limits
        # The longest window bounds how far back an admission can still matter.
        self._longest_window = max(w for _, w in app_limits)
        # region -> admission timestamps (monotonic)
        self._admitted: dict[str, deque[float]] = {}
        # region -> unblock timestamp (monotonic), set by 429 Retry-After
        self._blocked_until: dict[str, float] = {}
        # regions whose window log has been oriented from server counts once
        self._seeded: set[str] = set()

    async def acquire(self, region: str) -> None:
        """Acquire permission to make one request. Blocks until every window has a slot."""
        longest = self._longest_window
        while True:
            now = time.monotonic()
            blocked_until = self._blocked_until.get(region, 0.0)
            if now < blocked_until:
                await asyncio.sleep(blocked_until - now)
                continue

            dq = self._admitted.setdefault(region, deque())
            while dq and dq[0] <= now - longest:
                dq.popleft()

            wait = 0.0
            for limit, window in self._app_limits:
                in_window = [t for t in dq if t > now - window]
                if len(in_window) >= limit:
                    # Wait until enough of the oldest entries exit this window.
                    oldest_free = sorted(in_window)[len(in_window) - limit]
                    wait = max(wait, oldest_free + window - now)

            if wait <= 0:
                dq.append(now)  # claim; synchronous, so atomic on one event loop
                return

            logger.debug("Rate limit pacing for %s: waiting %.2fs", region, wait)
            await asyncio.sleep(wait)  # sleep holding nothing

    def block(self, region: str, seconds: float) -> None:
        """Block all admissions for `region` for `seconds` (429 Retry-After)."""
        self._blocked_until[region] = time.monotonic() + max(0.0, seconds)

    def seed_from_counts(self, region: str, counts: dict[int, int]) -> None:
        """Orient a fresh client from the server's own usage ledger (once per region).

        Riot reports your per-window usage in ``X-App-Rate-Limit-Count`` on
        every response. The client passes the parsed counts here on every
        fresh response; this pre-fills the window log on the first one, so a
        restarted client does not re-burst into a partially spent window.
        Later calls are no-ops. Assumes the current request was just admitted
        (it is already in the log and counted by the server).

        Riot's windows are nested — the calls counted in a shorter window
        are a subset of a longer window's count. Each counted request becomes
        one synthetic admission, banded by age at the *newest* timestamp
        consistent with the counts: the innermost band (shortest window) is
        placed at now, and each older band just outside the window below it.
        The seed is therefore pessimistic about the age of the counted
        requests: it can hold a slot longer than strictly needed, never
        shorter. For back-to-back script runs the extra wait is bounded by
        how old the previous run's calls were.
        """
        if region in self._seeded:
            return
        self._seeded.add(region)
        now = time.monotonic()
        dq = self._admitted.setdefault(region, deque())
        # (placed_at, n) per band, innermost (newest) first
        bands: list[tuple[float, int]] = []
        prev_window = 0
        prev_count = 1  # the current request is already in the log
        for _, window in sorted(self._app_limits, key=lambda lw: lw[1]):
            count = max(counts.get(window, 0), prev_count)
            bands.append((now - prev_window, max(count - prev_count, 0)))
            prev_window, prev_count = window, count
        # append oldest-first, then restore chronological order (the real
        # current entry was appended before the seed). Mutate the deque in
        # place so any concurrent acquire holding a reference to it sees the
        # same log — a rebind could orphan a parked admission mid-check.
        for placed_at, n in reversed(bands):
            dq.extend([placed_at] * n)
        ordered = sorted(dq)
        dq.clear()
        dq.extend(ordered)
        logger.info("Oriented %s rate limits from server counts: %s", region, counts)
