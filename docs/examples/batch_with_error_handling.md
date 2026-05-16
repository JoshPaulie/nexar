# Batch With Error Handling

`get_players()` raises `BatchError` when some players fail to fetch. The exception provides both `errors` and `successful_results`.

```py
-8<-- "examples/batch_with_error_handling.py"
```
