import json
import math
from unittest.mock import Mock

import pytest
from requests import Response

from emtl import core
from emtl.const import _urls


def response(value=None, text=None, status=200):
    result = Response()
    result.status_code = status
    result._content = (json.dumps(value) if text is None else text).encode()
    return result


def test_login(monkeypatch, fake_captcha):
    monkeypatch.setenv("EM_USERNAME", " P0_FAKE_USER ")
    monkeypatch.setenv("EM_PASSWORD", " P0_FAKE_PASSWORD ")
    encrypt = Mock(return_value="P0_FAKE_ENCRYPTED")
    monkeypatch.setattr(core, "emt_trade_encrypt", encrypt)
    session = Mock()
    session.post.return_value = response({"Status": 0})
    session.get.return_value = response(text='id="em_validatekey" type="hidden" value=" P0_FAKE_TOKEN "')
    monkeypatch.setattr(core, "session", session)
    assert core.login(duration=9) == "P0_FAKE_TOKEN"
    encrypt.assert_called_once_with("P0_FAKE_PASSWORD")
    args, kwargs = session.post.call_args
    assert args == (_urls["login"],)
    assert kwargs["data"] == {
        "userId": "P0_FAKE_USER",
        "password": "P0_FAKE_ENCRYPTED",
        "randNumber": 0.5,
        "identifyCode": 1234,
        "duration": 9,
        "authCode": "",
        "type": "Z",
        "secInfo": "",
    }
    assert kwargs["headers"]["X-Requested-With"] == "XMLHttpRequest"
    assert core._em_validate_key == "P0_FAKE_TOKEN"


@pytest.mark.parametrize(
    ("name", "tag", "args"),
    [
        ("query_asset_and_position", "query_asset_and_pos", ()),
        ("query_orders", "query_orders", ()),
        ("query_trades", "query_trades", ()),
        ("query_history_orders", "query_his_orders", (10, "start", "end")),
        ("query_history_trades", "query_his_trades", (10, "start", "end")),
        ("query_funds_flow", "query_funds_flow", (10, "start", "end")),
    ],
)
def test_queries(monkeypatch, name, tag, args):
    value = {"Status": -1, "Data": [{"nested": "P0_FAKE_RESPONSE"}]}
    session = Mock()
    session.post.return_value = response(value)
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P0_FAKE_TOKEN")
    login = Mock(side_effect=AssertionError("unexpected login"))
    monkeypatch.setattr(core, "login", login)
    assert getattr(core, name)(*args) == value
    sent_args, sent_kwargs = session.post.call_args
    assert sent_args == (_urls[tag] + "P0_FAKE_TOKEN",)
    assert sent_kwargs["data"] == ({"qqhs": 10, "dwc": "", "st": "start", "et": "end"} if args else {"qqhs": 100, "dwc": ""})
    assert sent_kwargs["headers"]["X-Requested-With"] == "XMLHttpRequest"
    login.assert_not_called()


def test_auto_login_and_order(monkeypatch):
    monkeypatch.setattr(core, "login", Mock(return_value="P0_FAKE_TOKEN"))
    session = Mock()
    result = response({"Status": -1, "Data": {"x": 1}})
    result.json = Mock(side_effect=[{"first": 1}, {"Status": -1, "Data": {"x": 1}}])
    session.post.return_value = result
    monkeypatch.setattr(core, "session", session)
    assert core.create_order("FAKE", "B", "SA", 5.01, 100) == {"Status": -1, "Data": {"x": 1}}
    assert result.json.call_count == 2
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["create_order"] + "P0_FAKE_TOKEN",)
    assert session.post.call_args.kwargs["data"] == {
        "stockCode": "FAKE",
        "tradeType": "B",
        "zqmc": "",
        "market": "SA",
        "price": 5.01,
        "amount": 100,
    }


def test_cancel_order(monkeypatch):
    session = Mock()
    session.post.return_value = response(text=" P0_FAKE_ORDER \n")
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P0_FAKE_TOKEN")
    assert core.cancel_order(" P0_FAKE_ORDER ") == "P0_FAKE_ORDER"
    assert session.post.call_args.kwargs["data"] == {"revokes": "P0_FAKE_ORDER"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ({}, None),
        ({"status": -1}, None),
        ({"status": 0, "realtimequote": {"currentPrice": " 1.25 "}}, 1.25),
        ({"status": 0, "realtimequote": {"currentPrice": " "}}, 0.0),
    ],
)
def test_last_price(monkeypatch, value, expected):
    session = Mock()
    session.get.return_value = response(value)
    monkeypatch.setattr(core, "session", session)
    actual = core.get_last_price(" FAKE ", "SA")
    assert math.isnan(actual) if expected is None else actual == expected
    assert session.get.call_args.kwargs["params"] == {"id": "FAKE", "market": "SA"}


def test_order_exception_is_not_retried(monkeypatch):
    session = Mock()
    session.post.side_effect = RuntimeError("P0_FAKE_EXCEPTION")
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P0_FAKE_TOKEN")
    with pytest.raises(RuntimeError, match="P0_FAKE_EXCEPTION"):
        core.create_order("FAKE", "B", "SA", 1.0, 100)
    session.post.assert_called_once()


def test_non_200_preserves_bare_raise():
    with pytest.raises(RuntimeError, match="No active exception"):
        core._check_resp(response(text="P0_FAKE_RESPONSE", status=500))


@pytest.mark.parametrize(
    ("username", "password", "expected_user", "expected_password"),
    [
        (" explicit ", "", "explicit", "env_password"),
        ("", " explicit ", "env_user", "explicit"),
    ],
)
def test_login_fallbacks(monkeypatch, fake_captcha, username, password, expected_user, expected_password):
    monkeypatch.setenv("EM_USERNAME", " env_user ")
    monkeypatch.setenv("EM_PASSWORD", " env_password ")
    encrypt = Mock(return_value="fake")
    monkeypatch.setattr(core, "emt_trade_encrypt", encrypt)
    session = Mock()
    session.post.return_value = response({})
    session.get.return_value = response(text="no token")
    monkeypatch.setattr(core, "session", session)
    assert core.login(username, password) is None
    assert session.post.call_args.kwargs["data"]["userId"] == expected_user
    encrypt.assert_called_once_with(expected_password)


def test_login_malformed_json_propagates(monkeypatch, fake_captcha):
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "fake")
    session = Mock()
    session.post.return_value = response(text="not JSON")
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(ValueError, match="Expecting value"):
        core.login("P0_FAKE_USER", "P0_FAKE_PASSWORD")
    session.get.assert_not_called()
