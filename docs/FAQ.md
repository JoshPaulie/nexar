# FAQ

## What is a PUUID?

A **P**layer **U**niversally **U**nique **Id**entifier (PUUID) is a unique string associated with a Riot account. They are always 78 characters long.

With the introduction of Riot IDs, Summoner IDs were deprecated. The PUUID is now the primary lookup key for most API endpoints.

!!! Note

    PUUIDs are encrypted per API key.
    
    This means the same user will have different PUUIDs depending on which API key is used to retrieve them.

    Generally, this does not affect typical usage. However, you cannot look up a user's PUUID with one API key and then use that PUUID as input with a different API key.

## What's up with regions?

Riot has poor decision making and introduced 2 types of regions, v4 and v5.

- **v4** was for older endpoints, and named like "na1", "euw1", etc.
- **v5** was for newer endpoints, and named like "americas", "europe", etc.

I've abstracted this away in Nexar. Just use the region you believe is correct and let Nexar decide which to use, depending on the endpoint. File an issue if you think Nexar is using the wrong region for an endpoint.
