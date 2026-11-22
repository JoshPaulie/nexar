"""Tests for the static champion map module."""

from nexar.champions import CHAMPION_NAMES, champion_name


class TestChampionNames:
    """The snapshot resolves ids offline; unknown ids degrade to None."""

    def test_known_id_resolves_its_name(self) -> None:
        """Jinx is id 222 in Data Dragon (the id the sandbox roster uses)."""
        assert champion_name(222) == "Jinx"
        assert CHAMPION_NAMES[222] == "Jinx"

    def test_unknown_id_is_none_not_a_raise(self) -> None:
        """A champion newer than the snapshot (or a game-mode id) resolves to None."""
        assert champion_name(999_999) is None

    def test_ids_cover_the_mastery_and_rotation_fixture_champions(self) -> None:
        """Every champion id the offline fixtures serve resolves a real name."""
        fixture_ids = [222, 103, 412, 99, 86, 64, 51, 14, 121, 61, 7, 875, 24, 157, 1, 9]
        for champion_id in fixture_ids:
            assert champion_name(champion_id) is not None, champion_id
