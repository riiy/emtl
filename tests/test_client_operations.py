import math
from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl import core
from emtl.const import _base_headers
from emtl.const import _urls
from tests.client_helpers import SYNTHETIC
from tests.client_helpers import memory_session
from tests.client_helpers import ready
from tests.client_helpers import token_reply
from tests.helpers import QUERY_CALLS
from tests.helpers import protocol_cases
from tests.helpers import response

OPERATIONS = [*QUERY_CALLS, ("create_order", (" P2_FAKE ", "B", "SA", 1.25, 100)), ("cancel_order", (" P2_FAKE_ORDER ",))]
TAGS = {
    "query_asset_and_position": "query_asset_and_pos",
    "query_history_orders": "query_his_orders",
    "query_history_trades": "query_his_trades",
}


@pytest.mark.parametrize(("name", "args"), QUERY_CALLS)
def test_six_queries_preserve_complete_request_and_json_identity(client_factory, name, args):
    client = ready(client_factory())
    value = ["P2_FAKE_OPAQUE_RESULT"]
    reply = response({})
    reply.json = Mock(return_value=value)
    client._session.post.return_value = reply
    before = _base_headers.copy()
    assert getattr(client, name)(*args) is value
    client._session.post.assert_called_once_with(
        _urls[TAGS.get(name, name)] + "P2_FAKE_TOKEN",
        headers=dict(before, **{"X-Requested-With": "XMLHttpRequest"}),
        data={"qqhs": 10, "dwc": "", "st": "start", "et": "end"} if args else {"qqhs": 100, "dwc": ""},
    )
    assert _base_headers == before
    reply.json.assert_called_once()


def test_explicit_empty_query_form_is_not_replaced(client_factory):
    client = ready(client_factory())
    client._session.post.return_value = response([])
    assert client._query_something("query_orders", {}).json() == []
    assert client._session.post.call_args.kwargs["data"] == {}
    client._session.post.assert_called_once()


@pytest.mark.parametrize(("name", "args"), QUERY_CALLS)
@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError])
def test_query_transport_failure_propagates_once(client_factory, name, args, error_type):
    client = ready(client_factory())
    error = error_type("P2_FAKE_ERROR")
    client._session.post.side_effect = error
    with pytest.raises(error_type) as caught:
        getattr(client, name)(*args)
    assert caught.value is error
    client._session.post.assert_called_once()
    assert client._state == "READY"
    assert client._token == SYNTHETIC


@pytest.mark.parametrize(("name", "args"), QUERY_CALLS)
@pytest.mark.parametrize(("kind", "error"), [("none", AttributeError), ("http", RuntimeError), ("json", ValueError)])
def test_query_invalid_response_preserves_exception(client_factory, name, args, kind, error):
    client = ready(client_factory())
    client._session.post.return_value = {"none": None, "http": response(status=503), "json": response(text="invalid")}[kind]
    with pytest.raises(error):
        getattr(client, name)(*args)
    client._session.post.assert_called_once()


@pytest.mark.parametrize("trade_type", ["B", "S"])
@pytest.mark.parametrize("case", ["order_response", "order_rejected"])
def test_order_form_rejection_and_two_json_evaluations(client_factory, trade_type, case):
    client = ready(client_factory())
    value = protocol_cases()[case]
    reply = response({})
    reply.json = Mock(side_effect=[{"first": "ignored"}, value])
    client._session.post.return_value = reply
    assert client.create_order(" P2_FAKE ", trade_type, "SA", 1.25, 100) is value
    assert reply.json.call_count == 2
    client._session.post.assert_called_once_with(
        _urls["create_order"] + "P2_FAKE_TOKEN",
        headers=dict(_base_headers, **{"X-Requested-With": "XMLHttpRequest"}),
        data={"stockCode": " P2_FAKE ", "tradeType": trade_type, "zqmc": "", "market": "SA", "price": 1.25, "amount": 100},
        allow_redirects=False,
    )


@pytest.mark.parametrize(("name", "args"), OPERATIONS[-2:])
@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError, requests.exceptions.ChunkedEncodingError])
def test_uncertain_submission_never_replays_or_compensates(client_factory, name, args, error_type):
    client = ready(client_factory())
    events = []
    error = error_type("P2_FAKE_RESPONSE_LOST")

    def post(*args, **kwargs):
        events.append("P2_FAKE_ACCEPTED")
        raise error

    client._session.post.side_effect = post
    with pytest.raises(error_type) as caught:
        getattr(client, name)(*args)
    assert caught.value is error
    assert events == ["P2_FAKE_ACCEPTED"]
    client._session.post.assert_called_once()
    client._session.get.assert_not_called()
    assert client._state == "READY"
    assert client._token == SYNTHETIC


@pytest.mark.parametrize(("name", "args"), OPERATIONS[-2:])
@pytest.mark.parametrize(("kind", "error"), [("none", AttributeError), ("http", RuntimeError)])
def test_order_bad_response_never_retries(client_factory, name, args, kind, error):
    client = ready(client_factory())
    client._session.post.return_value = None if kind == "none" else response(status=500)
    with pytest.raises(error):
        getattr(client, name)(*args)
    client._session.post.assert_called_once()
    client._session.get.assert_not_called()


@pytest.mark.parametrize("index", [1, 2])
def test_order_each_json_failure_propagates_without_retry(client_factory, index):
    client = ready(client_factory())
    error = ValueError("P2_FAKE_JSON")
    reply = response({})
    reply.json = Mock(side_effect=[error] if index == 1 else [{}, error])
    client._session.post.return_value = reply
    with pytest.raises(ValueError, match="P2_FAKE_JSON") as caught:
        client.create_order("FAKE", "S", "SA", 1, 100)
    assert caught.value is error
    assert reply.json.call_count == index
    client._session.post.assert_called_once()


@pytest.mark.parametrize(("order", "text", "expected"), [(" ", " ", ""), (" P2_FAKE_ORDER ", " rejected \n", "rejected")])
def test_cancel_request_and_text_result_remain_uninterpreted(client_factory, order, text, expected):
    client = ready(client_factory())
    client._session.post.return_value = response(text=text)
    assert client.cancel_order(order) == expected
    client._session.post.assert_called_once_with(
        _urls["cancel_order"] + "P2_FAKE_TOKEN",
        headers=dict(_base_headers, **{"X-Requested-With": "XMLHttpRequest"}),
        data={"revokes": order.strip()},
        allow_redirects=False,
    )


def test_cancel_text_failure_propagates_once(client_factory, monkeypatch):
    client = ready(client_factory())
    error = requests.exceptions.ChunkedEncodingError("P2_FAKE_TEXT")
    reply = response(text="unused")
    text = PropertyMock(side_effect=error)
    monkeypatch.setattr(type(reply), "text", text)
    client._session.post.return_value = reply
    with pytest.raises(type(error)) as caught:
        client.cancel_order(" P2_FAKE_ORDER ")
    assert caught.value is error
    client._session.post.assert_called_once()
    text.assert_called_once_with()


@pytest.mark.parametrize(("name", "args"), OPERATIONS[-2:])
@pytest.mark.parametrize("status", [307, 308])
def test_redirect_cannot_resend_order_at_adapter_level(client_factory, name, args, status):
    def redirect(request):
        reply = response(status=status)
        reply.headers["Location"] = "https://example.invalid/P2_FAKE_REDIRECT"
        return reply

    session, adapter = memory_session(redirect)
    client = ready(client_factory(session=session))
    with pytest.raises(RuntimeError, match="No active exception"):
        getattr(client, name)(*args)
    assert len(adapter.requests) == 1
    assert adapter.requests[0].method == "POST"
    assert adapter.requests[0].url == _urls[name] + "P2_FAKE_TOKEN"


@pytest.mark.parametrize(("name", "args"), OPERATIONS)
def test_wrapper_none_seam_is_only_a_return_contract(client_factory, monkeypatch, name, args):
    client = ready(client_factory())
    query = Mock(return_value=None)
    monkeypatch.setattr(client, "_query_something", query)
    assert getattr(client, name)(*args) is None
    query.assert_called_once()
    client._session.post.assert_not_called()  # not counted as no-retry evidence


@pytest.mark.parametrize(("name", "args"), OPERATIONS)
def test_false_response_executes_actual_request_chain(client_factory, name, args):
    class FalseResponse(requests.Response):
        def __bool__(self):
            return False

    reply = FalseResponse()
    reply.status_code = 200
    reply.json = Mock(side_effect=AssertionError("must not parse"))
    client = ready(client_factory())
    client._session.post.return_value = reply
    assert getattr(client, name)(*args) is None
    client._session.post.assert_called_once()
    reply.json.assert_not_called()


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (None, None),
        ({}, None),
        ({"status": -1}, None),
        ({"status": 0, "realtimequote": {"currentPrice": " 1.25 "}}, 1.25),
        ({"status": 0, "realtimequote": {"currentPrice": " "}}, 0.0),
    ],
)
def test_market_price_uses_own_session_without_login(client_factory, payload, expected):
    client = client_factory()
    client._session.get.return_value = response(payload)
    actual = client.get_last_price(" FAKE ", "SA")
    assert math.isnan(actual) if expected is None else actual == expected
    client._session.get.assert_called_once_with(
        "https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot", params={"id": "FAKE", "market": "SA"}, headers=_base_headers
    )
    client._session.post.assert_not_called()
    assert client._state == "NEW"


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"status": 0}, KeyError),
        ({"status": 0, "realtimequote": {}}, KeyError),
        ({"status": 0, "realtimequote": {"currentPrice": "invalid"}}, ValueError),
        ({"status": 0, "realtimequote": {"currentPrice": None}}, AttributeError),
    ],
)
def test_market_price_bad_data_is_not_swallowed(client_factory, payload, error):
    client = client_factory()
    client._session.get.return_value = response(payload)
    with pytest.raises(error):
        client.get_last_price(" FAKE ", "SA")
    client._session.get.assert_called_once()


@pytest.mark.parametrize("kind", ["timeout", "connection", "http", "json"])
def test_market_price_transport_and_decode_errors_are_not_nan(client_factory, kind):
    client = client_factory()
    error = None
    if kind in {"timeout", "connection"}:
        error = (requests.Timeout if kind == "timeout" else requests.ConnectionError)("P2_FAKE_ERROR")
        client._session.get.side_effect = error
        expected = type(error)
    else:
        client._session.get.return_value = response(text="invalid", status=503 if kind == "http" else 200)
        expected = RuntimeError if kind == "http" else ValueError
    with pytest.raises(expected) as caught:
        client.get_last_price("FAKE", "SA")
    if error is not None:
        assert caught.value is error
    client._session.get.assert_called_once()


@pytest.mark.parametrize(("name", "args"), OPERATIONS)
def test_legacy_and_client_protocol_parity(client_factory, monkeypatch, name, args):
    client = ready(client_factory())
    legacy = Mock()
    monkeypatch.setattr(core, "session", legacy)
    monkeypatch.setattr(core, "_em_validate_key", "P2_FAKE_TOKEN")
    for session in (legacy, client._session):
        session.post.return_value = response(text=" rejected \n") if name == "cancel_order" else response({"Status": -1, "Data": []})
    assert getattr(core, name)(*args) == getattr(client, name)(*args)
    old, new = legacy.post.call_args, client._session.post.call_args
    expected_kwargs = dict(old.kwargs)
    if name in {"create_order", "cancel_order"}:
        expected_kwargs["allow_redirects"] = False
    assert new.args == old.args
    assert new.kwargs == expected_kwargs
    legacy.post.assert_called_once()
    client._session.post.assert_called_once()


def test_initial_order_authentication_post_is_distinct_from_submission(client_factory):
    client = client_factory()
    client._session.get.side_effect = [response(text="P2_FAKE_IMAGE"), token_reply()]
    client._session.post.side_effect = [response({"Status": 0}), response({"Status": -1})]
    assert client.create_order("FAKE", "B", "SA", 1, 100) == {"Status": -1}
    urls = [entry.args[0] for entry in client._session.post.call_args_list]
    assert urls == [_urls["login"], _urls["create_order"] + "P2_FAKE_TOKEN"]
    assert client._session.post.call_args_list[1].kwargs["allow_redirects"] is False


def test_legacy_bare_raise_still_reraises_an_active_exception():
    error = ValueError("P2_FAKE_ACTIVE_EXCEPTION")
    try:
        raise error
    except ValueError:
        with pytest.raises(ValueError, match="P2_FAKE_ACTIVE_EXCEPTION") as caught:
            core._check_resp(response(status=500))
    assert caught.value is error
