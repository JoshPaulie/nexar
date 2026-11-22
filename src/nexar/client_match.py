"""Match-v5 lookups for NexarClient."""

from datetime import UTC, datetime
from typing import cast

from .core import NexarCore
from .enums import MatchType, Queue, Region
from .models import Match, Timeline

MAX_MATCH_ID_COUNT = 100
DEFAULT_MATCH_ID_COUNT = 20


class MatchMixin(NexarCore):
    """Match-v5 lookups."""

    # Match API
    async def get_match(self, match_id: str, region: Region | None = None) -> Match:
        """Get one match by its match-v5 id (e.g. ``NA1_1234567890``)."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region)
        return Match.from_api_response(data)

    async def get_match_timeline(self, match_id: str, region: Region | None = None) -> Timeline:
        """Get a match's timeline: per-minute participant frames plus the event stream."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}/timeline"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region)
        return Timeline.from_api_response(data)

    async def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = DEFAULT_MATCH_ID_COUNT,
        region: Region | None = None,
    ) -> list[str]:
        """Get a page of a player's match ids.

        ``start`` skips into the history and ``count`` caps the page at
        ``MAX_MATCH_ID_COUNT`` (100) per call, defaulting to
        ``DEFAULT_MATCH_ID_COUNT`` (20).
        """
        if start < 0:
            msg = f"start must be non-negative, got {start}"
            raise ValueError(msg)
        if not 0 <= count <= MAX_MATCH_ID_COUNT:
            msg = f"count must be between 0 and {MAX_MATCH_ID_COUNT}"
            raise ValueError(msg)

        resolved_region = self._resolve_region(region)
        params = self._build_match_ids_params(start_time, end_time, queue, match_type, start, count)
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region, params=params)
        return cast("list[str]", data)

    def _build_match_ids_params(
        self,
        start_time: int | datetime | None,
        end_time: int | datetime | None,
        queue: Queue | int | None,
        match_type: MatchType | str | None,
        start: int,
        count: int,
    ) -> dict[str, int | str]:
        params: dict[str, int | str] = {}
        if start_time is not None:
            params["startTime"] = self._to_epoch(start_time)
        if end_time is not None:
            params["endTime"] = self._to_epoch(end_time)
        if queue is not None:
            params["queue"] = queue.value if isinstance(queue, Queue) else queue
        if match_type is not None:
            params["type"] = match_type.value if isinstance(match_type, MatchType) else match_type
        if start != 0:
            params["start"] = start
        if count != DEFAULT_MATCH_ID_COUNT:
            params["count"] = count
        return params

    @staticmethod
    def _to_epoch(value: int | datetime) -> int:
        """
        Convert int or datetime to UTC epoch seconds.

        Naive datetimes are treated as UTC.
        """
        if isinstance(value, int):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return int(value.timestamp())
