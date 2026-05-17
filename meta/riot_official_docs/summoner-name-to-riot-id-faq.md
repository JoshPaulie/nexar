Summoner Name to Riot ID

### LAST UPDATED: October 30, 2023

## FAQ

### Is there an endpoint to get Summoner Name by Riot ID or Riot ID by Summoner Name?

Unfortunately, no. We currently have no plans to add riotIdName or riotIdTagline on League endpoints.

We recommend having your own database of players (summonerID + puuid). This lookup creates new players on your end.

### What are the rules for allowing special characters in RiotIDs (Game Name + Tagline)?

Game names are 3-16 characters long. Do not use the `#` symbol. This is the separator between Game Name and Tagline.

Tagline is 3-5 alphanumeric characters. Any Unicode **letter** is supported in both fields.

### When will summonerName fields be removed from raw-matches?

There is no ETA on removing Summoner Names. However, the SummonerName field will be stale, containing old data, as of November 20, 2023. After that date, RiotID will be the preferred player identification.

We encourage you to change from Summoner Names to RiotID as soon as possible.

### Will League API keys get a rate limit increase to compensate for additional calls?

This will be reviewed on a case-by-case basis. If you find you are hitting your rate limit, please reach out to us via the developer portal at [https://developer.riotgames.com](https://developer.riotgames.com/).

### Will each player still be tied to a specific region ID, even though we no longer look up by Summoner Name + Region ID?

Yes, all player data will continue to be sharded to the League region.

### What is the best way to look up the League Region ID associated with a Riot ID?

We are working to improve active-shards coverage. Unfortunately, we do not have an ETA for completion. We recommend changing your forms from Region + Summoner Name to Region + Riot ID until this feature is complete.

After this is released, you will be able to take only the RiotID as input from players.

For general questions regarding the Summoner Name to Riot ID transition, please check out the [Support Team FAQ](https://support-leagueoflegends.riotgames.com/hc/en-us/articles/20616577122707-Summoner-Name-to-Riot-ID-Transition-FAQ).
