# Batch With Error Handling

`get_players()` raises `BatchError` when some players fail to fetch. The exception provides both `errors` and `successful_results`. `Player.get_matches()` follows the same contract: if one match id fails to fetch, the matches that did load are carried on the raised `BatchError` instead of being discarded.

```py
--8<-- "examples/batch_with_error_handling.py"
```
