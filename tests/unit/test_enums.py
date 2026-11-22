"""Unit tests for enum properties and methods."""

import logging

import pytest

from nexar.enums import MapId, MatchParticipantPosition, Queue, RankDivision, RankTier, Region


class TestRegion:
    def test_account_region(self) -> None:
        assert Region.NA1.account_region == "americas"
        assert Region.KR.account_region == "asia"
        assert Region.EUW1.account_region == "europe"

    def test_all_regions_have_v5_region(self) -> None:
        for region in Region:
            assert region.v5_region in {"americas", "asia", "europe", "sea"}

    def test_all_regions_have_account_region(self) -> None:
        for region in Region:
            assert region.account_region in {"americas", "asia", "europe"}

    def test_me1_region_routing(self) -> None:
        """ME1 (Middle East & North Africa) routes via the europe cluster."""
        assert Region.ME1.v5_region == "europe"
        assert Region.ME1.account_region == "europe"

    def test_deprecated_platforms_removed(self) -> None:
        """PH2 and TH2 moved into SG2 (2025-01-08) and are off the executable surface."""
        assert "PH2" not in Region.__members__
        assert "TH2" not in Region.__members__


class TestQueue:
    def test_is_ranked_solo(self) -> None:
        assert Queue.RANKED_SOLO_5x5.is_ranked is True

    def test_is_ranked_flex(self) -> None:
        assert Queue.RANKED_FLEX_SR.is_ranked is True

    def test_is_not_ranked(self) -> None:
        assert Queue.ARAM.is_ranked is False
        assert Queue.QUICKPLAY.is_ranked is False

    def test_get_ranked_queues(self) -> None:
        ranked = Queue.get_ranked_queues()
        assert ranked == (Queue.RANKED_SOLO_5x5, Queue.RANKED_FLEX_SR)

    def test_solo_queue_alias(self) -> None:
        """The alias must be the same enum member, not a value-equal twin."""
        assert Queue.SOLO_QUEUE is Queue.RANKED_SOLO_5x5

    def test_flex_queue_alias(self) -> None:
        assert Queue.FLEX_QUEUE is Queue.RANKED_FLEX_SR


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        (RankTier.IRON, "Iron"),
        (RankTier.BRONZE, "Bronze"),
        (RankTier.SILVER, "Silver"),
        (RankTier.GOLD, "Gold"),
        (RankTier.PLATINUM, "Platinum"),
        (RankTier.EMERALD, "Emerald"),
        (RankTier.DIAMOND, "Diamond"),
        (RankTier.MASTER, "Master"),
        (RankTier.GRANDMASTER, "Grandmaster"),
        (RankTier.CHALLENGER, "Challenger"),
    ],
)
def test_rank_tier_str(tier: RankTier, expected: str) -> None:
    assert str(tier) == expected


class TestUnknownQueue:
    def test_unknown_queue_returns_unknown_sentinel(self, caplog: pytest.LogCaptureFixture) -> None:
        """Queue(1750) should return Queue.UNKNOWN instead of raising, at DEBUG."""
        # The fallback record is expected noise, so it logs at DEBUG — below
        # the default WARNING root level, hence the explicit set_level here.
        # The level is part of the pin: at WARNING this test must fail.
        caplog.set_level(logging.DEBUG, logger="nexar")
        result = Queue(1750)
        assert result is Queue.UNKNOWN
        records = [r for r in caplog.records if r.name == "nexar" and "Unknown queue ID" in r.getMessage()]
        assert records
        assert all(r.levelname == "DEBUG" for r in records)


class TestUnknownMapId:
    def test_unknown_map_id_returns_unknown_sentinel(self, caplog: pytest.LogCaptureFixture) -> None:
        """MapId(999) should return MapId.UNKNOWN instead of raising."""
        result = MapId(999)
        assert result is MapId.UNKNOWN
        assert "Unknown map ID encountered: 999" in caplog.text


class TestUnknownPosition:
    def test_unknown_position_string_returns_empty_sentinel(self, caplog: pytest.LogCaptureFixture) -> None:
        """An unrecognized position string degrades to EMPTY instead of aborting the whole match parse."""
        result = MatchParticipantPosition("SOME_NEW_POSITION")
        assert result is MatchParticipantPosition.EMPTY
        assert "Unknown participant position encountered: SOME_NEW_POSITION" in caplog.text


class TestRankDivision:
    def test_str(self) -> None:
        assert str(RankDivision.ONE) == "I"
        assert str(RankDivision.TWO) == "II"
        assert str(RankDivision.THREE) == "III"
        assert str(RankDivision.FOUR) == "IV"
