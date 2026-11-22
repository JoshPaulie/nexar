"""ChampionStats and RoleStats derived values — tables next to the models they pin."""

import pytest

from nexar.models.stats import ChampionStats, PerformanceStats, RoleStats


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            {
                "champion_id": 1,
                "champion_name": "Annie",
                "games_played": 5,
                "wins": 5,
                "losses": 0,
                "total_kills": 50,
                "total_deaths": 5,
                "total_assists": 25,
            },
            {"win_rate": 1.0, "avg_kills": 10.0, "avg_deaths": 1.0, "avg_assists": 5.0},
        ),
        (
            {
                "champion_id": 42,
                "champion_name": "Corki",
                "games_played": 20,
                "wins": 12,
                "losses": 8,
                "total_kills": 240,
                "total_deaths": 160,
                "total_assists": 300,
            },
            {"win_rate": 0.6, "avg_kills": 12.0, "avg_deaths": 8.0, "avg_assists": 15.0, "avg_kda": 3.375},
        ),
        (
            {
                "champion_id": 1,
                "champion_name": "Annie",
                "games_played": 3,
                "wins": 3,
                "losses": 0,
                "total_kills": 15,
                "total_deaths": 0,
                "total_assists": 30,
            },
            # (15 + 30) / max(0, 1) == 45.0, mirroring Participant.kda()
            {"avg_kda": 45.0},
        ),
        (
            {
                "champion_id": 1,
                "champion_name": "Annie",
                "games_played": 2,
                "wins": 1,
                "losses": 1,
                "total_kills": 10,
                "total_deaths": 4,
                "total_assists": 6,
            },
            {"avg_kda": 4.0},
        ),
    ],
    ids=["perfect-record", "realistic-record", "zero-deaths-perfect-kda", "with-deaths"],
)
def test_champion_stats_derived_values(record: dict, expected: dict) -> None:
    stats = ChampionStats(**record)
    for field, value in expected.items():
        assert getattr(stats, field) == value


@pytest.mark.parametrize(
    "field",
    ["win_rate", "avg_kda", "avg_kills", "avg_deaths", "avg_assists"],
)
def test_zero_games_properties_report_zero_not_a_division(field: str) -> None:
    """A zero-games record reads 0.0 off every derived property, never a ZeroDivisionError.

    The numerators are nonzero on purpose: a guard that only held for all-zero
    inputs would pass here while an avg_kda of 5.0 leaked through.
    """
    stats = ChampionStats(
        champion_id=1,
        champion_name="Annie",
        games_played=0,
        wins=0,
        losses=0,
        total_kills=10,
        total_deaths=3,
        total_assists=5,
    )

    assert getattr(stats, field) == 0.0


@pytest.mark.parametrize(
    "field",
    ["win_rate", "avg_kda", "avg_kills", "avg_deaths", "avg_assists"],
)
def test_role_stats_zero_games_report_zero_not_a_division(field: str) -> None:
    """A zero-games role record reads 0.0 off every derived property, never a ZeroDivisionError.

    Mirrors the ChampionStats table: nonzero numerators, so a guard that only
    held for all-zero inputs cannot pass while a real ratio leaks through.
    """
    stats = RoleStats(
        role="TOP",
        games_played=0,
        wins=0,
        total_kills=10,
        total_deaths=3,
        total_assists=5,
    )

    assert getattr(stats, field) == 0.0


def test_performance_stats_empty_is_all_zero() -> None:
    """The empty factory reports zero games and zero averages for the no-match case."""
    assert PerformanceStats.empty() == PerformanceStats(
        total_games=0,
        wins=0,
        losses=0,
        win_rate=0.0,
        avg_kills=0.0,
        avg_deaths=0.0,
        avg_assists=0.0,
        avg_kda=0.0,
        avg_cs=0.0,
        avg_game_duration_minutes=0.0,
    )
