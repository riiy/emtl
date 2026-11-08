"""P3 risk signals through the real public chain and synthetic Session only."""

import logging
from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl.const import _urls
from emtl.errors import BrokerHTTPError
from emtl.errors import TradeOutcomeUnknown
from tests.client_helpers import SYNTHETIC
from tests.client_helpers import ready
from tests.client_helpers import token_reply
from tests.helpers import assert_no_sensitive_logs
from tests.helpers import response

TRADES = [("create_order", ("P3_FAKE_STOCK", "B", "SA", 1, 100)), ("cancel_order", (" P3_FAKE_ORDER ",))]


def assert_unknown(error, operation, reason, status=None):
    assert type(error) is TradeOutcomeUnknown
    assert error.operation == operation
    assert error.reason == reason
    assert error.status_code == status
    assert error.__cause__ is None
    assert error.__suppress_context__ is True


def assert_one_trade(session, operation):
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls[operation] + SYNTHETIC,)
    assert session.post.call_args.kwargs["allow_redirects"] is False
    session.get.assert_not_called()
    assert [str(entry[0]) for entry in session.mock_calls] == ["post"]


@pytest.mark.parametrize("operation", ["create_order", "cancel_order"])
@pytest.mark.parametrize("reason", ["exchange_error", "http_status", "response_error"])
def test_public_error_contract(operation, reason):
    status = 503 if reason == "http_status" else None
    error = TradeOutcomeUnknown(operation, reason, status)
    assert type(error).__bases__ == (RuntimeError,)
    assert (error.operation, error.reason, error.status_code) == (operation, reason, status)
    assert error.args == (str(error),)
    assert "do not automatically resubmit" in str(error)
    http = BrokerHTTPError(503)
    assert type(http).__bases__ == (RuntimeError,)
    assert http.status_code == 503
    assert not isinstance(error, BrokerHTTPError)


@pytest.mark.parametrize("status", [True, 200.0, "P3_FAKE_SECRET", object()])
def test_error_rejects_non_integer_status_without_echo(status):
    for make in (lambda: BrokerHTTPError(status), lambda: TradeOutcomeUnknown("create_order", "http_status", status)):
        with pytest.raises(TypeError, match="^invalid HTTP status$"):
            make()


@pytest.mark.parametrize(
    "args",
    [("bad", "exchange_error"), ("create_order", "bad"), ("create_order", "http_status", 200), ("cancel_order", "response_error", 503)],
)
def test_invalid_trade_error_fields(args):
    with pytest.raises(ValueError, match="invalid trade error fields|HTTP status must not be 200|status is only valid for http_status"):
        TradeOutcomeUnknown(*args)


@pytest.mark.parametrize(("operation", "args"), TRADES)
def test_k1_auth_timeout_is_not_trade_unknown(client_factory, operation, args):
    client = client_factory()
    session = client._session
    session.get.return_value = response(text="P3_FAKE_IMAGE")
    error = requests.Timeout("P3_FAKE_AUTH_ERROR")

    def post(url, **kwargs):
        assert url == _urls["login"]
        session.cookies.set("attempt", "P3_FAKE_COOKIE")
        raise error

    session.post.side_effect = post
    with pytest.raises(requests.Timeout) as caught:
        getattr(client, operation)(*args)
    assert caught.value is error
    assert not isinstance(caught.value, TradeOutcomeUnknown)
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["login"],)
    session.get.assert_called_once()
    assert session.get.call_args.args[0].startswith(_urls["yzm"])
    assert [entry[0] for entry in session.mock_calls] == ["get", "post"]
    assert client._state == "FAILED"
    assert client._token == ""
    assert not session.cookies
    before = list(session.mock_calls)
    with pytest.raises(RuntimeError, match="^authentication required$") as caught:
        getattr(client, operation)(*args)
    assert type(caught.value) is RuntimeError
    assert session.mock_calls == before


@pytest.mark.parametrize(("operation", "args"), TRADES)
def test_k2_ready_timeout_has_one_attempt_and_no_compensation(client_factory, operation, args):
    client = ready(client_factory())
    entered = []

    def post(url, **kwargs):
        entered.append(url)
        raise requests.Timeout("P3_FAKE_LOST_RESPONSE")

    client._session.post.side_effect = post
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "exchange_error")
    assert entered == [_urls[operation] + SYNTHETIC]
    assert_one_trade(client._session, operation)
    assert (client._state, client._token) == ("READY", SYNTHETIC)


@pytest.mark.parametrize("stage", ["json2", "text"])
def test_k3_decode_after_post_is_unknown(client_factory, monkeypatch, stage):
    client = ready(client_factory())
    reply = response({})
    error = ValueError("P3_FAKE_DECODE")
    operation, args = TRADES[stage == "text"]
    if stage == "json2":
        reply.json = Mock(side_effect=[{}, error])
    else:
        text = PropertyMock(side_effect=error)
        monkeypatch.setattr(type(reply), "text", text)
    client._session.post.return_value = reply
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "response_error")
    assert_one_trade(client._session, operation)
    if stage == "json2":
        assert reply.json.call_count == 2
    else:
        text.assert_called_once_with()


@pytest.mark.parametrize("value", [{"Status": -1, "Data": ["P3_FAKE_OPAQUE"]}, ["P3_FAKE_LIST"], None])
def test_k4_second_json_is_returned_without_interpretation(client_factory, value):
    client = ready(client_factory())
    reply = response({})
    reply.json = Mock(side_effect=[{"first": True}, value])
    client._session.post.return_value = reply
    assert client.create_order(*TRADES[0][1]) is value
    assert reply.json.call_count == 2
    assert_one_trade(client._session, "create_order")


@pytest.mark.parametrize("text", [" rejected \n", " "])
def test_k4_cancel_text_is_not_interpreted(client_factory, text):
    client = ready(client_factory())
    client._session.post.return_value = response(text=text)
    assert client.cancel_order(*TRADES[1][1]) == text.strip()
    assert_one_trade(client._session, "cancel_order")


@pytest.mark.parametrize(("operation", "args"), TRADES)
def test_auto_auth_then_trade_timeout_classifies_only_trade(client_factory, operation, args):
    client = client_factory()
    session = client._session
    session.get.side_effect = [response(text="P3_FAKE_IMAGE"), token_reply()]
    session.post.side_effect = [response({"Status": 0}), requests.Timeout("P3_FAKE_TRADE")]
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "exchange_error")
    assert [entry.args[0] for entry in session.post.call_args_list] == [_urls["login"], _urls[operation] + SYNTHETIC]
    assert [entry[0] for entry in session.mock_calls] == ["get", "post", "get", "post"]
    assert session.get.call_args_list[0].args[0].startswith(_urls["yzm"])
    assert session.get.call_args_list[1].args == ("https://jywg.18.cn/Trade/Buy",)
    assert (client._state, client._token) == ("READY", SYNTHETIC)


@pytest.mark.parametrize(("operation", "args"), TRADES)
@pytest.mark.parametrize("status", [400, 503, 307, 308, 201, -1])
def test_non_200_is_unknown_without_parsing_or_redirect(client_factory, operation, args, status):
    client = ready(client_factory())
    reply = response(status=status)
    reply.json = Mock(side_effect=AssertionError("must not decode"))
    client._session.post.return_value = reply
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "http_status", status)
    reply.json.assert_not_called()
    assert_one_trade(client._session, operation)


class UntrustedStatus:
    def __str__(self):
        raise AssertionError("must not format status")

    __repr__ = __str__

    def __eq__(self, other):
        raise AssertionError("must not compare status")


class BrokenStatus:
    @property
    def status_code(self):
        raise ValueError("P3_FAKE_STATUS_SECRET")


@pytest.mark.parametrize(("operation", "args"), TRADES)
@pytest.mark.parametrize("kind", ["none", "missing", "getter", "string", "bool", "float", "untrusted"])
def test_invalid_response_after_post_is_exchange_error(client_factory, operation, args, kind):
    client = ready(client_factory())
    replies = {"none": None, "missing": object(), "getter": BrokenStatus()}
    reply = response({})
    reply.status_code = {"string": "P3_FAKE_STATUS_SECRET", "bool": True, "float": 200.0, "untrusted": UntrustedStatus()}.get(kind)
    client._session.post.return_value = replies.get(kind, reply)
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "exchange_error")
    assert_one_trade(client._session, operation)


@pytest.mark.parametrize("stage", ["json1", "bool", "strip", "missing_json", "missing_text", "log"])
def test_result_stage_failures_are_unknown(client_factory, monkeypatch, stage):
    from emtl import client as client_module

    client = ready(client_factory())
    error = ValueError("P3_FAKE_RESULT")
    operation, args = TRADES[stage in {"strip", "missing_text"}]
    reply = response({})
    if stage == "json1":
        reply.json = Mock(side_effect=error)
    elif stage == "bool":
        monkeypatch.setattr(type(reply), "__bool__", Mock(side_effect=error))
    elif stage == "strip":
        monkeypatch.setattr(type(reply), "text", PropertyMock(return_value=Mock(strip=Mock(side_effect=error))))
    elif stage.startswith("missing"):
        reply = type("MissingResult", (), {"status_code": 200})()
    else:
        monkeypatch.setattr(client_module.logger, "info", Mock(side_effect=error))
    client._session.post.return_value = reply
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "response_error")
    assert_one_trade(client._session, operation)
    if stage == "json1":
        reply.json.assert_called_once()


@pytest.mark.parametrize(("operation", "args"), TRADES)
@pytest.mark.parametrize("stage", ["closed", "failed", "token_missing", "request_form"])
def test_pre_boundary_failure_is_not_unknown(client_factory, operation, args, stage):
    client = ready(client_factory())
    session = client._session
    if stage == "closed":
        client.close()
        session.reset_mock()
    elif stage == "failed":
        client._state = "FAILED"
    elif stage == "token_missing":
        client._token = ""
    else:
        client._token = object()  # URL construction must fail before the sending callback.
    with pytest.raises(TypeError if stage == "request_form" else RuntimeError) as caught:
        getattr(client, operation)(*args)
    assert type(caught.value) is (TypeError if stage == "request_form" else RuntimeError)
    session.get.assert_not_called()
    session.post.assert_not_called()


def test_attempt_marker_does_not_leak_to_next_call(client_factory):
    client = ready(client_factory())
    client._session.post.side_effect = requests.Timeout("P3_FAKE_FIRST")
    with pytest.raises(TradeOutcomeUnknown):
        client.create_order(*TRADES[0][1])
    before = list(client._session.mock_calls)
    with pytest.raises(AttributeError) as caught:
        client.cancel_order(None)
    assert type(caught.value) is AttributeError
    assert client._session.mock_calls == before


def test_explicit_query_after_unknown_is_not_automatic_recovery(client_factory):
    client = ready(client_factory())
    client._session.cookies.set("attempt", "P3_FAKE_COOKIE")
    client._session.post.side_effect = requests.Timeout("P3_FAKE_FIRST")
    with pytest.raises(TradeOutcomeUnknown):
        client.create_order(*TRADES[0][1])
    assert_one_trade(client._session, "create_order")
    assert (client._state, client._token) == ("READY", SYNTHETIC)
    assert client._session.cookies.get("attempt") == "P3_FAKE_COOKIE"
    client._session.post.side_effect = None
    value = ["P3_FAKE_QUERY"]
    client._session.post.return_value = response(value)
    assert client.query_orders() == value
    assert [entry.args[0] for entry in client._session.post.call_args_list] == [
        _urls["create_order"] + SYNTHETIC,
        _urls["query_orders"] + SYNTHETIC,
    ]
    client._session.get.assert_not_called()


@pytest.mark.parametrize("status", [True, 200.0, "P3_FAKE_STATUS_SECRET", UntrustedStatus()])
def test_non_trade_invalid_status_is_safe_type_error(client_factory, status):
    client = ready(client_factory())
    reply = response({})
    reply.status_code = status
    client._session.post.return_value = reply
    with pytest.raises(TypeError, match="^invalid HTTP status$") as caught:
        client.query_orders()
    assert type(caught.value) is TypeError
    client._session.post.assert_called_once()


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
@pytest.mark.parametrize(("operation", "args"), TRADES)
def test_process_control_is_not_converted_or_replayed(client_factory, operation, args, error_type):
    client = ready(client_factory())
    error = error_type()
    client._session.post.side_effect = error
    with pytest.raises(error_type) as caught:
        getattr(client, operation)(*args)
    assert caught.value is error
    assert_one_trade(client._session, operation)


def test_exact_builtin_error_fields_only():
    class Substring(str):
        pass

    class Subint(int):
        pass

    for operation, reason in [(Substring("create_order"), "exchange_error"), ("create_order", Substring("exchange_error")), (None, None)]:
        with pytest.raises(TypeError, match="^invalid trade error fields$"):
            TradeOutcomeUnknown(operation, reason)
    with pytest.raises(TypeError):
        BrokerHTTPError(Subint(503))
    with pytest.raises(ValueError, match="^HTTP status must not be 200$"):
        BrokerHTTPError(200)


def test_failure_acquiring_post_callable_is_before_boundary(client_factory):
    class Session:
        def __init__(self):
            self.cookies = requests.cookies.RequestsCookieJar()
            self.get = Mock()
            self.close = Mock()
            self.fail = False
            self.post_calls = Mock()

        @property
        def post(self):
            if self.fail:
                raise AttributeError("P3_FAKE_POST_LOOKUP")
            return self.post_calls

    session = Session()
    client = ready(client_factory(session=session))
    session.fail = True
    with pytest.raises(AttributeError, match="^P3_FAKE_POST_LOOKUP$") as caught:
        client.create_order(*TRADES[0][1])
    assert type(caught.value) is AttributeError
    session.get.assert_not_called()
    session.post_calls.assert_not_called()


@pytest.mark.parametrize("stage", ["json1", "json2", "log", "text"])
def test_response_broker_http_error_is_not_exchange_http_status(client_factory, monkeypatch, caplog, stage):
    from emtl import client as client_module

    client = ready(client_factory())
    error = BrokerHTTPError(503)
    reply = response({})
    operation, args = TRADES[stage == "text"]
    if stage == "json1":
        reply.json = Mock(side_effect=error)
    elif stage == "json2":
        reply.json = Mock(side_effect=[{}, error])
    elif stage == "text":
        text = PropertyMock(side_effect=error)
        monkeypatch.setattr(type(reply), "text", text)
    else:
        reply.json = Mock(return_value={})
    client._session.post.return_value = reply

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            raise error

    handler = BrokenHandler()
    if stage == "log":
        caplog.set_level(logging.INFO, logger=client_module.logger.name)
        client_module.logger.addHandler(handler)
    try:
        with pytest.raises(TradeOutcomeUnknown) as caught:
            getattr(client, operation)(*args)
    finally:
        if stage == "log":
            client_module.logger.removeHandler(handler)
        handler.close()
    assert_unknown(caught.value, operation, "response_error")
    assert reply.status_code == 200
    assert_one_trade(client._session, operation)
    if stage == "text":
        text.assert_called_once_with()
    else:
        assert reply.json.call_count == (2 if stage == "json2" else 1)
    assert (client._state, client._token) == ("READY", SYNTHETIC)


@pytest.mark.parametrize("operation", ["create_order", "cancel_order"])
@pytest.mark.parametrize("stage", ["post", "status_getter", "http_log"])
def test_trade_http_status_requires_response_source(client_factory, caplog, operation, stage):
    from emtl import client as client_module

    caplog.set_level(logging.DEBUG)
    secrets = {
        name: f"P3_R2_FAKE_{name}_SECRET" for name in ("USER", "PASSWORD", "COOKIE", "AUTH", "REQUEST_BODY", "RESPONSE_BODY", "NOTE")
    }
    client = ready(client_factory(secrets["USER"], secrets["PASSWORD"]))
    session = client._session
    session.cookies.set("r2", secrets["COOKIE"])
    session.headers.update({"Cookie": secrets["COOKIE"], "Authorization": secrets["AUTH"]})
    error = BrokerHTTPError(401)
    error.add_note(secrets["NOTE"])
    reply = response({"echo": secrets["RESPONSE_BODY"]}, status=503)
    reply.json = Mock(side_effect=AssertionError("must not decode"))
    reads = []

    class GetterFailure:
        @property
        def status_code(self):
            reads.append("status")
            raise error

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            assert record.msg == "request failed, code=%s"
            assert record.args == (503,)
            raise error

    handler = BrokenHandler()
    if stage == "post":
        session.post.side_effect = error
    elif stage == "status_getter":
        session.post.return_value = GetterFailure()
    else:
        session.post.return_value = reply
        client_module.logger.addHandler(handler)
    args = (secrets["REQUEST_BODY"], "B", "SA", 1, 100) if operation == "create_order" else (secrets["REQUEST_BODY"],)
    try:
        with pytest.raises(TradeOutcomeUnknown) as caught:
            getattr(client, operation)(*args)
    finally:
        if stage == "http_log":
            client_module.logger.removeHandler(handler)
        handler.close()
    assert_one_trade(session, operation)
    assert (client._state, client._token) == ("READY", SYNTHETIC)
    assert session.cookies.get("r2") == secrets["COOKIE"]
    assert reads == (["status"] if stage == "status_getter" else [])
    reply.json.assert_not_called()
    assert_no_sensitive_logs(caplog.records, [*secrets.values(), SYNTHETIC])
    assert_unknown(
        caught.value, operation, "http_status" if stage == "http_log" else "exchange_error", 503 if stage == "http_log" else None
    )


@pytest.mark.parametrize(("operation", "args"), TRADES)
def test_trade_status_is_read_once_and_does_not_leak_to_next_call(client_factory, operation, args):
    client = ready(client_factory())
    session = client._session
    reads = []

    class OneStatus:
        @property
        def status_code(self):
            reads.append("status")
            assert len(reads) == 1
            return 503

    session.post.return_value = OneStatus()
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "http_status", 503)
    assert reads == ["status"]
    assert_one_trade(session, operation)
    session.reset_mock()
    session.post.side_effect = BrokerHTTPError(401)
    with pytest.raises(TradeOutcomeUnknown) as caught:
        getattr(client, operation)(*args)
    assert_unknown(caught.value, operation, "exchange_error")
    assert_one_trade(session, operation)
    assert (client._state, client._token) == ("READY", SYNTHETIC)
