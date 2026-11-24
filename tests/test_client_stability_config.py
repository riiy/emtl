"""Validate explicit client settings without constructing transport resources."""

from unittest.mock import Mock

import pytest

from emtl import TradingClient


@pytest.mark.parametrize("field", ["connect_timeout", "read_timeout", "captcha_read_timeout"])
@pytest.mark.parametrize("value", [None, True, "5", 0, -1, float("inf"), float("nan"), 10**400])
def test_invalid_timeout_fails_before_resource_creation(field, value):
    factory = Mock()
    with pytest.raises(ValueError, match="positive finite"):
        TradingClient("P2_FAKE_A", "P2_FAKE_PASSWORD", session_factory=factory, **{field: value})
    factory.assert_not_called()


@pytest.mark.parametrize("value", [None, True, "5", 0, -1, 1.5])
def test_invalid_captcha_limit_fails_before_resource_creation(value):
    factory = Mock()
    with pytest.raises(ValueError, match="positive integer"):
        TradingClient("P2_FAKE_A", "P2_FAKE_PASSWORD", session_factory=factory, captcha_max_attempts=value)
    factory.assert_not_called()
