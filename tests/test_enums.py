"""Tests for enums."""

from nexar.enums import Division, Queue, RegionV4, RegionV5, Tier


class TestRegionV4:
    """Test RegionV4 enum."""

    def test_region_v4_values(self):
        """Test that RegionV4 has expected values."""
        assert RegionV4.NA1.value == "na1"
        assert RegionV4.EUW1.value == "euw1"
        assert RegionV4.KR.value == "kr"

    def test_all_regions_present(self):
        """Test that all expected regions are present."""
        expected_regions = {
            "BR1",
            "EUN1",
            "EUW1",
            "JP1",
            "KR",
            "LA1",
            "LA2",
            "NA1",
            "OC1",
            "PH2",
            "RU",
            "SG2",
            "TH2",
            "TR1",
            "TW2",
            "VN2",
        }
        actual_regions = {region.name for region in RegionV4}
        assert actual_regions == expected_regions


class TestRegionV5:
    """Test RegionV5 enum."""

    def test_region_v5_values(self):
        """Test that RegionV5 has expected values."""
        assert RegionV5.AMERICAS.value == "americas"
        assert RegionV5.EUROPE.value == "europe"
        assert RegionV5.ASIA.value == "asia"
        assert RegionV5.SEA.value == "sea"

    def test_all_regions_present(self):
        """Test that all expected regions are present."""
        expected_regions = {"AMERICAS", "ASIA", "EUROPE", "SEA"}
        actual_regions = {region.name for region in RegionV5}
        assert actual_regions == expected_regions


class TestQueue:
    """Test Queue enum."""

    def test_queue_values(self):
        """Test that Queue has expected values."""
        assert Queue.RANKED_SOLO_5x5.value == "RANKED_SOLO_5x5"
        assert Queue.RANKED_FLEX_SR.value == "RANKED_FLEX_SR"


class TestTier:
    """Test Tier enum."""

    def test_tier_values(self):
        """Test that Tier has expected values."""
        assert Tier.IRON.value == "IRON"
        assert Tier.CHALLENGER.value == "CHALLENGER"

    def test_all_tiers_present(self):
        """Test that all expected tiers are present."""
        expected_tiers = {
            "IRON",
            "BRONZE",
            "SILVER",
            "GOLD",
            "PLATINUM",
            "EMERALD",
            "DIAMOND",
            "MASTER",
            "GRANDMASTER",
            "CHALLENGER",
        }
        actual_tiers = {tier.name for tier in Tier}
        assert actual_tiers == expected_tiers


class TestDivision:
    """Test Division enum."""

    def test_division_values(self):
        """Test that Division has expected values."""
        assert Division.ONE.value == "I"
        assert Division.TWO.value == "II"
        assert Division.THREE.value == "III"
        assert Division.FOUR.value == "IV"
