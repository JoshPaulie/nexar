"""Account-related models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RiotAccount:
    """Represents a Riot account."""

    puuid: str
    """
    Player Universally Unique Identifier.
    
    Check out docs/puuid.md for more.
    """

    game_name: str
    """
    Game name associated with Riot account, if a name is set.
    
    ```
    bexli#bex
    ^^^^^
    ```
    """

    tag_line: str
    """
    Tag line associated with Riot account, if a tag line is set.
    
    ```
    bexli#bex
          ^^^
    ```
    """

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
    """(Deprecated) Summoner ID."""

    puuid: str
    """
    Player Universally Unique Identifier.
    
    Check out docs/puuid.md for more.
    """

    profile_icon_id: int
    """ID of the summoner icon associated with the summoner."""

    @property
    def profile_icon_url(self):
        """Link to profile icon URL via CDragon."""
        return (
            f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
            f"global/default/v1/profile-icons/{self.profile_icon_id}.jpg"
        )

    revision_date: datetime
    """
    Date summoner was last modified specified as datetime.
    
    The following events will update this timestamp:
        - profile icon change
        - playing the tutorial or advanced tutorial
        - finishing a game
        - summoner name change
    """

    summoner_level: int
    """Summoner level associated with the summoner."""

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
