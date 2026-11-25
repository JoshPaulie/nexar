"""Example: choosing where the SQLite cache lives."""

from nexar.cache import CacheConfig

config = CacheConfig(
    backend="sqlite",
    cache_name="my_app_cache",  # Creates my_app_cache.sqlite
    cache_dir="./cache",  # Saves to ./cache/my_app_cache.sqlite
)
