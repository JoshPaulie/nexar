"""Tests for rate limit configuration options."""

import pytest

from nexar import NexarClient
from nexar.rate_limiter import PERSONAL_LIMITS, PRODUCTION_LIMITS, _validate_rate_limit


class TestRateLimitConfiguration:
    def test_default_personal_limits(self) -> None:
        client = NexarClient(riot_api_key="test")
        assert client.rate_limiter._app_limits == PERSONAL_LIMITS

    def test_custom_production_limits(self) -> None:
        client = NexarClient(riot_api_key="test", app_rate_limits=PRODUCTION_LIMITS)
        assert client.rate_limiter._app_limits == PRODUCTION_LIMITS

    def test_custom_limits(self) -> None:
        client = NexarClient(riot_api_key="test", app_rate_limits=((100, 5), (1000, 60)))
        assert client.rate_limiter._app_limits == ((100, 5), (1000, 60))

    def test_validate_rate_limit_valid(self) -> None:
        _validate_rate_limit(20, 1)
        _validate_rate_limit(500, 10)
        _validate_rate_limit(30000, 600)

    def test_validate_rate_limit_zero_limit(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_rate_limit(0, 1)

    def test_validate_rate_limit_negative_limit(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_rate_limit(-5, 1)

    def test_validate_rate_limit_zero_window(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_rate_limit(20, 0)

    def test_validate_rate_limit_negative_window(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _validate_rate_limit(20, -5)

    def test_validate_rate_limit_suspiciously_high(self) -> None:
        with pytest.raises(ValueError, match="suspiciously high"):
            _validate_rate_limit(2000000, 1)

    def test_validate_rate_limit_suspiciously_long_window(self) -> None:
        with pytest.raises(ValueError, match="suspiciously long"):
            _validate_rate_limit(100, 90000)

    def test_no_key_type_parameter(self) -> None:
        client = NexarClient(riot_api_key="test-key")
        assert client.rate_limiter._app_limits == PERSONAL_LIMITS
