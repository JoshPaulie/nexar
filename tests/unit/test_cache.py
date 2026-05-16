"""Unit tests for cache configuration."""

from pathlib import Path

import pytest
from aiohttp_client_cache.backends import DictCache  # type: ignore[attr-defined]
from aiohttp_client_cache.backends.sqlite import SQLiteBackend

from nexar.cache import (
    DEFAULT_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    CacheConfig,
    create_cache_backend,
)


class TestCreateCacheBackend:
    def test_sqlite_backend(self, tmp_path: Path) -> None:
        config = CacheConfig(backend="sqlite", cache_name="test", cache_dir=str(tmp_path))
        backend = create_cache_backend(config)
        assert isinstance(backend, SQLiteBackend)
        assert backend.expire_after == 3600

    def test_memory_backend(self) -> None:
        config = CacheConfig(backend="memory")
        backend = create_cache_backend(config)
        assert isinstance(backend, DictCache)

    def test_invalid_backend_raises(self) -> None:
        config = CacheConfig(backend="invalid")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unsupported cache backend"):
            create_cache_backend(config)


class TestCacheConfigDefaults:
    def test_default_config_is_enabled(self) -> None:
        assert DEFAULT_CACHE_CONFIG.enabled is True

    def test_no_cache_config_is_disabled(self) -> None:
        assert NO_CACHE_CONFIG.enabled is False
