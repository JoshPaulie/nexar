"""
Rate limit quota assurance shared between dogfood bowls and integration tests.

Call :func:`ensure_rate_limit_quota` before making any real Riot API calls.
This reads ``/tmp/nexar-last-ran.txt`` and blocks until at least 125 seconds
have elapsed since the previous dogfood bowl or integration test run, giving
the in-memory rate limiter a full quota window to work with.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger("nexar.quota")

_LOCK_FILE = Path("/tmp/nexar-last-ran.txt")
_QUOTA_WINDOW = 125  # seconds between real-API-call runs


def ensure_rate_limit_quota() -> None:
    """
    Block until the rate-limit quota window has elapsed since the last run.

    Reads the timestamp from ``/tmp/nexar-last-ran.txt``.  If it's been
    fewer than 125 seconds, sleeps for the remainder.  If the file is
    missing, empty, or corrupt, proceeds immediately.
    """
    try:
        with _LOCK_FILE.open() as f:
            content = f.read().strip()
            if not content:
                logger.info("Lock file is empty — proceeding immediately.")
                return
            last_ts = float(content)
    except FileNotFoundError:
        logger.info("No lock file found — first run, proceeding immediately.")
        return
    except (ValueError, OSError) as exc:
        logger.warning("Could not read lock file (%s) — proceeding immediately.", exc)
        return

    elapsed = time.time() - last_ts
    if elapsed < _QUOTA_WINDOW:
        delay = _QUOTA_WINDOW - elapsed
        logger.info(
            "Last run was %.0fs ago — sleeping %.0fs to respect quota window (%ds).",
            elapsed,
            delay,
            _QUOTA_WINDOW,
        )
        time.sleep(delay)
    else:
        logger.info("Quota window satisfied (%.0fs since last run).", elapsed)


def write_last_ran() -> None:
    """Write the current timestamp to ``/tmp/nexar-last-ran.txt``."""
    try:
        with _LOCK_FILE.open("w") as f:
            f.write(f"{time.time():.0f}\n")
    except OSError as exc:
        logger.warning("Failed to write lock file: %s", exc)
