# Batch With Error Handling

[`get_players()`][nexar.client.NexarClient.get_players] raises [`BatchError`][nexar.exceptions.BatchError] when some players fail to fetch. The exception provides both `errors` and `successful_results`. Each entry in `errors` is keyed by the Riot ID string that was passed in, so read the key as a string. [`Player.get_matches()`][nexar.models.player.Player.get_matches] follows the same contract: if one match id fails to fetch, the matches that did load are carried on the raised [`BatchError`][nexar.exceptions.BatchError] instead of being discarded.

```py
--8<-- "examples/batch_with_error_handling.py"
```
