"""Champion-mastery fixture: one recorded entry in the wire shape."""

from typing import Any


def champion_mastery_payload(**overrides: object) -> dict[str, Any]:
    """Champion mastery entry in the recorded API shape (Riot omits empty values)."""
    data: dict[str, Any] = {
        "puuid": "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA",
        "championId": 7,
        "championLevel": 7,
        "championPoints": 127530,
        "championPointsSinceLastLevel": 2690,
        "championPointsUntilNextLevel": 1470,
        "chestGranted": True,
        "lastPlayTime": 1735112400000,
        "markRequiredForNextLevel": 2,
        "championSeasonMilestone": 8,
        "milestoneGrades": ["S", "S-"],
        "nextSeasonMilestone": {
            "requireGradeCounts": {"S-": 1, "S": 2},
            "rewardMarks": 2,
            "bonus": False,
            "rewardConfig": {
                "rewardValue": "MASTERY_CHEST",
                "rewardType": "CHEST",
                "maximumReward": 1,
            },
        },
    }
    data.update(overrides)
    return data
