"""Account-related models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RiotAccount:
    """Represents a Riot account."""

    puuid: str
    game_name: str
    tag_line: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "RiotAccount":
        """Create RiotAccount from API response."""
        return cls(
            puuid=data["puuid"], game_name=data["gameName"], tag_line=data["tagLine"]
        )


@dataclass(frozen=True)
class Summoner:
    """Represents a League of Legends summoner."""

    id: str
    puuid: str
    profile_icon_id: int
    revision_date: datetime  # Last modification date of summoner
    summoner_level: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Summoner":
        """Create Summoner from API response."""
        return cls(
            id=data["id"],
            puuid=data["puuid"],
            profile_icon_id=data["profileIconId"],
            revision_date=datetime.fromtimestamp(data["revisionDate"] / 1000),
            summoner_level=data["summonerLevel"],
        )
