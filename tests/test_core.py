import math
from unittest.mock import Mock

import pytest
import requests

from emtl import core
from emtl.const import _base_headers
from emtl.const import _urls
from tests.helpers import QUERY_CALLS
from tests.helpers import response


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
        "identifyCode": "1234",
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
    session.post.assert_called_once()
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


@pytest.mark.parametrize(("name", "args"), QUERY_CALLS)
@pytest.mark.parametrize("error", [requests.Timeout("P1_FAKE"), requests.ConnectionError("P1_FAKE")])
def test_query_transport_error_propagates(monkeypatch, error, name, args):
    session = Mock(post=Mock(side_effect=error))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    with pytest.raises(type(error)) as caught:
        getattr(core, name)(*args)
    assert caught.value is error
    session.post.assert_called_once()


@pytest.mark.parametrize(
    ("reply", "error"), [(None, AttributeError), (response(status=500), RuntimeError), (response(text="invalid"), ValueError)]
)
@pytest.mark.parametrize(("name", "args"), QUERY_CALLS)
def test_query_invalid_response(monkeypatch, reply, error, name, args):
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    with pytest.raises(error):
        getattr(core, name)(*args)
    session.post.assert_called_once()


def test_explicit_empty_query_form(monkeypatch):
    session = Mock(post=Mock(return_value=response([])))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    before = _base_headers.copy()
    assert core._query_something("query_orders", {}).json() == []
    assert session.post.call_args.kwargs["data"] == {}
    session.post.assert_called_once()
    assert _base_headers == before
    assert session.post.call_args.kwargs["headers"] == dict(before, **{"X-Requested-With": "XMLHttpRequest"})


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ({"status": 0}, KeyError),
        ({"status": 0, "realtimequote": {}}, KeyError),
        ({"status": 0, "realtimequote": {"currentPrice": "invalid"}}, ValueError),
        ({"status": 0, "realtimequote": {"currentPrice": None}}, AttributeError),
    ],
)
def test_price_invalid_data(monkeypatch, value, error):
    session = Mock(get=Mock(return_value=response(value)))
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(error):
        core.get_last_price(" FAKE ", "SA")
    session.get.assert_called_once()
    assert session.get.call_args.kwargs["params"] == {"id": "FAKE", "market": "SA"}


@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError])
def test_price_transport_error_is_not_nan(monkeypatch, error_type):
    """Regression for the reviewed mutation that swallowed transport failures."""
    error = error_type("P1_FAKE_PRICE_ERROR")
    session = Mock(get=Mock(side_effect=error))
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(error_type) as caught:
        core.get_last_price(" FAKE ", "SA")
    assert caught.value is error
    session.get.assert_called_once_with(
        "https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot",
        params={"id": "FAKE", "market": "SA"},
        headers=_base_headers,
    )


@pytest.mark.parametrize(
    ("status", "text", "error", "message"),
    [
        (503, "P1_FAKE_BODY", RuntimeError, "No active exception"),
        (200, "P1_FAKE_INVALID_JSON", requests.exceptions.JSONDecodeError, "Expecting value"),
    ],
)
def test_price_response_error_is_not_nan(monkeypatch, status, text, error, message):
    reply = response(text=text, status=status)
    reply.json = Mock(wraps=reply.json)
    session = Mock(get=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(error, match=message):
        core.get_last_price(" FAKE ", "SA")
    session.get.assert_called_once_with(
        "https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot",
        params={"id": "FAKE", "market": "SA"},
        headers=_base_headers,
    )
    assert reply.json.call_count == (1 if status == 200 else 0)
