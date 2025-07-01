import os
import sys

from nexar.client import NexarClient, Region

riot_api_key = os.getenv("RIOT_API_KEY")
if riot_api_key is None:
    sys.exit("Couldn't find Riot api key variable.")

# Example usage - replace with your actual API key and region
client = NexarClient(
    riot_api_key=riot_api_key,
    default_v4_region=Region.v4.NA1,
    default_v5_region=Region.v5.AMERICAS,
)

# Example API call
print(client.get_riot_account("bexli", "bex"))
