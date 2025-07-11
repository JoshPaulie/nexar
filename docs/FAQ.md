# FAQ

## What is a PUUID?

A **P**layer **U**niversally **U**nique **Id**entifier (PUUID) is a unique string associated with a Riot account. They are always 78 characters long.

With the introduction of Riot IDs, Summoner IDs were deprecated. The PUUID is now the primary lookup key for most API endpoints.

!!! Note

    PUUIDs are encrypted per API key.
    
    This means the same user will have different PUUIDs depending on which API key is used to retrieve them.

    Generally, this does not affect typical usage. However, you cannot look up a user's PUUID with one API key and then use that PUUID as input with a different API key.

## Why do I have to provide 2 regions?

Under the hood, Nexar is of course making API calls to various Riot endpoints. Some are using "V4" regions, while newer are using "V5" regions. Each endpoint uses a different "version" region.

Despite none of the endpoints ever using both the region versions, Nexar's `Player` object makes calls with methods which may use one or the other. Thus, both need set when defining a player.
