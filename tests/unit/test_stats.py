"""ChampionStats derived values — one table next to the model they pin."""

import pytest

from nexar.models.stats import ChampionStats


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
