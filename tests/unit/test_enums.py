"""Unit tests for enum properties and methods."""

from nexar.enums import (
    MapId,
    Queue,
    RankDivision,
    RankTier,
    Region,
)


class TestRegion:
    def test_v5_region(self) -> None:
        assert Region.NA1.v5_region == "americas"
        assert Region.KR.v5_region == "asia"
        assert Region.EUW1.v5_region == "europe"
        assert Region.OC1.v5_region == "sea"

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
        assert Queue.SOLO_QUEUE.value == Queue.RANKED_SOLO_5x5.value

    def test_flex_queue_alias(self) -> None:
        assert Queue.FLEX_QUEUE.value == Queue.RANKED_FLEX_SR.value


class TestRankTier:
    def test_str(self) -> None:
        assert str(RankTier.IRON) == "Iron"
        assert str(RankTier.BRONZE) == "Bronze"
        assert str(RankTier.SILVER) == "Silver"
        assert str(RankTier.GOLD) == "Gold"
        assert str(RankTier.PLATINUM) == "Platinum"
        assert str(RankTier.EMERALD) == "Emerald"
        assert str(RankTier.DIAMOND) == "Diamond"
        assert str(RankTier.MASTER) == "Master"
        assert str(RankTier.GRANDMASTER) == "Grandmaster"
        assert str(RankTier.CHALLENGER) == "Challenger"


class TestUnknownQueue:
    def test_unknown_queue_returns_unknown_sentinel(self, caplog) -> None:
        """Queue(1750) should return Queue.UNKNOWN instead of raising."""
        result = Queue(1750)
        assert result is Queue.UNKNOWN
        assert "Unknown queue ID encountered: 1750" in caplog.text


class TestUnknownMapId:
    def test_unknown_map_id_returns_unknown_sentinel(self, caplog) -> None:
        """MapId(999) should return MapId.UNKNOWN instead of raising."""
        result = MapId(999)
        assert result is MapId.UNKNOWN
        assert "Unknown map ID encountered: 999" in caplog.text


class TestRankDivision:
    def test_str(self) -> None:
        assert str(RankDivision.ONE) == "I"
        assert str(RankDivision.TWO) == "II"
        assert str(RankDivision.THREE) == "III"
        assert str(RankDivision.FOUR) == "IV"
