import logging
import traceback
from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl import client as client_module
from emtl import core
from emtl.const import _urls
from emtl.errors import BrokerHTTPError
from emtl.errors import TradeOutcomeUnknown
from tests.client_helpers import SYNTHETIC
from tests.client_helpers import ready
from tests.client_helpers import token_reply
from tests.helpers import assert_no_sensitive_logs
from tests.helpers import response


@pytest.mark.parametrize(
    "stage", ["login", "rejected", "missing", "login_json", "query", "http", "create", "cancel", "json", "text", "ocr"]
)
def test_client_does_not_log_secrets_in_success_or_failure(client_factory, monkeypatch, caplog, stage):
    caplog.set_level(logging.DEBUG)
    secrets = {
        name: f"P2_FAKE_{name}_SECRET" for name in ("USER", "PASSWORD", "ENCRYPTED", "TOKEN", "COOKIE", "AUTH", "CODE", "BODY", "ERROR")
    }
    client = client_factory(secrets["USER"], secrets["PASSWORD"])
    session = client._session
    session.headers.update({"Cookie": secrets["COOKIE"], "Authorization": secrets["AUTH"]})
    session.cookies.set("p2", secrets["COOKIE"])
    monkeypatch.setattr(client_module, "emt_trade_encrypt", Mock(return_value=secrets["ENCRYPTED"]))
    monkeypatch.setattr(client_module, "SystemRandom", Mock(return_value=Mock(random=Mock(return_value=0.5))))
    login = response({"Status": 0, "echo": secrets["BODY"]})
    business = response({"Status": -1, "echo": secrets["BODY"]})
    for reply in (login, business):
        reply.url = "https://example.invalid/?validatekey=" + secrets["TOKEN"]
        reply.headers["Set-Cookie"] = secrets["COOKIE"]
    session.get.side_effect = [response(text=secrets["BODY"]), token_reply(secrets["TOKEN"])]
    session.post.return_value = login
    if stage in {"login", "rejected", "missing", "login_json", "ocr"}:
        if stage == "rejected":
            login._content = b'{"Status":-1}'
        elif stage == "missing":
            session.get.side_effect = [response(text="fake"), response(text=secrets["BODY"])]
        elif stage == "login_json":
            login.json = Mock(side_effect=ValueError(secrets["ERROR"]))
        elif stage == "ocr":
            client._ocr_factory = lambda: Mock(classification=Mock(side_effect=[secrets["CODE"], "1234"]))
            session.get.side_effect = [response(text="one"), response(text="two"), token_reply(secrets["TOKEN"])]
        if stage == "login_json":
            with pytest.raises(ValueError, match="P2_FAKE_ERROR_SECRET"):
                client.login()
        else:
            result = client.login()
            assert result == (None if stage in {"rejected", "missing"} else secrets["TOKEN"])
        session.post.assert_called_once()
    else:
        ready(client, secrets["TOKEN"])
        session.post.return_value = business
        if stage == "query":
            assert client.query_orders()["echo"] == secrets["BODY"]
        elif stage == "http":
            business.status_code = 503
            with pytest.raises(BrokerHTTPError) as caught:
                client.query_orders()
            assert type(caught.value) is BrokerHTTPError
            assert caught.value.status_code == 503
        else:
            error = requests.Timeout(secrets["ERROR"]) if stage in {"create", "cancel"} else ValueError(secrets["ERROR"])
            if stage in {"create", "cancel"}:
                session.post.side_effect = error
            elif stage == "json":
                business.json = Mock(side_effect=[{}, error])
            else:
                monkeypatch.setattr(type(business), "text", PropertyMock(side_effect=error))

            def invoke():
                if stage in {"create", "json"}:
                    return client.create_order(secrets["BODY"], "B", "SA", 1, 100)
                return client.cancel_order(secrets["BODY"])

            with pytest.raises(TradeOutcomeUnknown) as caught:
                invoke()
            assert type(caught.value) is TradeOutcomeUnknown
            assert caught.value.reason == ("exchange_error" if stage in {"create", "cancel"} else "response_error")
            assert caught.value.status_code is None
        session.post.assert_called_once()
    assert_no_sensitive_logs(caplog.records, list(secrets.values()))
    assert not any(secret in repr(client) for secret in secrets.values())


def test_fixed_sdk_exceptions_do_not_echo_credentials_or_token(client_factory):
    client = client_factory("P2_FAKE_USER_SECRET", "P2_FAKE_PASSWORD_SECRET")
    client._state = "FAILED"
    synthetic = "P2_FAKE_TOKEN_SECRET"
    client._token = synthetic
    with pytest.raises(RuntimeError) as caught:
        client.query_orders()
    assert str(caught.value) == "authentication required"
    client.close()
    with pytest.raises(RuntimeError) as caught:
        client.login()
    assert str(caught.value) == "client is closed"


@pytest.mark.parametrize("stage", ["transport", "json2", "text", "trade_http", "auth_http", "active_http"])
def test_new_errors_and_standard_traceback_do_not_expose_secrets(client_factory, monkeypatch, caplog, stage):
    caplog.set_level(logging.DEBUG)
    secrets = {
        name: f"P3_FAKE_{name}_SENTINEL"
        for name in ("USER", "PASSWORD", "CODE", "TOKEN", "COOKIE", "AUTH", "REQUEST_BODY", "RESPONSE_BODY", "ERROR", "NOTE", "CAUSE")
    }
    client = client_factory(secrets["USER"], secrets["PASSWORD"])
    session = client._session
    session.headers.update({"Cookie": secrets["COOKIE"], "Authorization": secrets["AUTH"]})
    session.cookies.set("p3", secrets["COOKIE"])
    error = requests.Timeout(secrets["ERROR"])
    error.add_note(secrets["NOTE"])
    error.__cause__ = ValueError(secrets["CAUSE"])
    reply = response({"echo": secrets["RESPONSE_BODY"]})
    reply.url = "https://example.invalid/?validatekey=" + secrets["TOKEN"]
    reply.headers["Set-Cookie"] = secrets["COOKIE"]
    session.post.return_value = reply
    if stage == "auth_http":
        reply.status_code = 503
        session.get.return_value = response(text=secrets["RESPONSE_BODY"])
        client._ocr_factory = lambda: Mock(classification=Mock(return_value="1234"))
        monkeypatch.setattr(client_module, "emt_trade_encrypt", Mock(return_value=secrets["PASSWORD"]))
        invoke = client.login
    else:
        ready(client, secrets["TOKEN"])
        if stage == "transport":
            session.post.side_effect = error
        elif stage == "json2":
            reply.json = Mock(side_effect=[{}, error])
        elif stage == "text":
            monkeypatch.setattr(type(reply), "text", PropertyMock(side_effect=error))
        else:
            reply.status_code = 503

        def invoke():
            if stage == "text":
                return client.cancel_order(secrets["REQUEST_BODY"])
            if stage == "active_http":
                return client.query_orders()
            return client.create_order(secrets["REQUEST_BODY"], "B", "SA", 1, 100)

    expected = BrokerHTTPError if stage in {"auth_http", "active_http"} else TradeOutcomeUnknown
    # An unrelated active exception must not appear in the new standard traceback.
    try:
        raise error
    except requests.Timeout:
        with pytest.raises(expected) as caught:
            invoke()
    new = caught.value
    assert type(new) is expected
    assert not any(hasattr(new, name) for name in ("request", "response", "original_error"))
    displayed = (str(new), repr(new), repr(new.args), repr(vars(new)), "".join(traceback.format_exception(new)))
    for text in displayed:
        assert not any(secret in text for secret in secrets.values())
    assert new.__cause__ is None
    assert new.__suppress_context__ is True
    assert_no_sensitive_logs(caplog.records, list(secrets.values()))
    session.post.assert_called_once()
    if stage != "auth_http":
        session.get.assert_not_called()
    else:
        assert client._state == "FAILED"
        assert client._token == ""
        assert not session.cookies


class HandlerAbortError(BaseException):
    pass


def _non_trade_http_failure(client_factory, stage):
    secrets = {name: f"P3_R3_FAKE_{name}_SECRET" for name in ("USER", "PASSWORD", "TOKEN", "COOKIE", "BODY", "MESSAGE", "NOTE", "CAUSE")}
    client = ready(client_factory(secrets["USER"], secrets["PASSWORD"]), secrets["TOKEN"])
    client._session.cookies.set("r3", secrets["COOKIE"])
    reply = response({"echo": secrets["BODY"]}, status=503)
    reply.json = Mock(side_effect=AssertionError("must not decode HTTP failure"))
    if stage == "query":
        client._session.post.return_value = reply
        invoke = client.query_orders
    elif stage == "market":
        client._session.get.return_value = reply

        def invoke():
            return client.get_last_price("P3_FAKE_SYMBOL", "SA")

    else:
        assert stage == "captcha"
        client._session.get.return_value = reply
        invoke = client.login
    return client, invoke, reply, secrets


def _assert_non_trade_http_attempt(client, reply, stage, secrets):
    session = client._session
    session.close.assert_not_called()
    reply.json.assert_not_called()
    if stage == "query":
        session.post.assert_called_once()
        assert session.post.call_args.args == (_urls["query_orders"] + secrets["TOKEN"],)
        session.get.assert_not_called()
        assert [entry[0] for entry in session.mock_calls] == ["post"]
    else:
        session.get.assert_called_once()
        session.post.assert_not_called()
        assert [entry[0] for entry in session.mock_calls] == ["get"]
        if stage == "captcha":
            assert session.get.call_args.args[0].startswith(_urls["yzm"])
            assert session.get.call_args.kwargs["timeout"] == 60
        else:
            assert session.get.call_args.args == ("https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot",)
    if stage == "captcha":
        assert (client._state, client._token) == ("FAILED", "")
        assert not session.cookies
        assert client._ocr is None
    else:
        assert (client._state, client._token) == ("READY", secrets["TOKEN"])
        assert session.cookies.get("r3") == secrets["COOKIE"]


@pytest.mark.parametrize("stage", ["captcha", "query", "market"])
@pytest.mark.parametrize("kind", ["broker", "value"])
def test_non_trade_http_error_survives_handler_failure(client_factory, caplog, stage, kind):
    caplog.set_level(logging.DEBUG)
    client, invoke, reply, secrets = _non_trade_http_failure(client_factory, stage)
    session = client._session
    original = BrokerHTTPError(401) if kind == "broker" else ValueError()
    original.args = (secrets["MESSAGE"],)
    original.add_note(secrets["NOTE"])
    original.__cause__ = ValueError(secrets["CAUSE"])
    emitted = []

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            emitted.append(record)
            raise original

    handler = BrokenHandler()
    client_module.logger.addHandler(handler)
    try:
        with pytest.raises(BrokerHTTPError) as caught:
            invoke()
    finally:
        client_module.logger.removeHandler(handler)
        handler.close()
    _assert_non_trade_http_attempt(client, reply, stage, secrets)
    assert client._session is session
    assert [(record.msg, record.args) for record in emitted] == [("request failed, code=%s", (503,))]
    new = caught.value
    assert type(new) is BrokerHTTPError
    assert new.status_code == 503
    assert new is not original
    assert not getattr(new, "__notes__", ())
    displayed = (str(new), repr(new), repr(new.args), repr(vars(new)), "".join(traceback.format_exception(new)))
    for text in displayed:
        assert not any(secret in text for secret in secrets.values())
    assert new.__cause__ is None
    assert new.__suppress_context__ is True
    assert_no_sensitive_logs([*caplog.records, *emitted], list(secrets.values()))


@pytest.mark.parametrize("stage", ["captcha", "query", "market"])
def test_non_trade_http_handler_base_exception_propagates(client_factory, caplog, stage):
    caplog.set_level(logging.DEBUG)
    client, invoke, reply, secrets = _non_trade_http_failure(client_factory, stage)
    original = HandlerAbortError(secrets["MESSAGE"])
    original.add_note(secrets["NOTE"])

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            raise original

    handler = BrokenHandler()
    client_module.logger.addHandler(handler)
    try:
        with pytest.raises(HandlerAbortError) as caught:
            invoke()
    finally:
        client_module.logger.removeHandler(handler)
        handler.close()
    assert caught.value is original
    _assert_non_trade_http_attempt(client, reply, stage, secrets)
    assert_no_sensitive_logs(caplog.records, list(secrets.values()))


def test_safe_http_error_is_established_before_logging(client_factory, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    client, invoke, reply, secrets = _non_trade_http_failure(client_factory, "query")
    events = []

    def observe_construction(status):
        events.append(("error", status))
        return BrokerHTTPError(status)

    monkeypatch.setattr(client_module, "BrokerHTTPError", observe_construction)

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            events.append(("log", record.args[0]))
            raise ValueError(secrets["MESSAGE"])

    handler = BrokenHandler()
    client_module.logger.addHandler(handler)
    try:
        with pytest.raises(BrokerHTTPError) as caught:
            invoke()
    finally:
        client_module.logger.removeHandler(handler)
        handler.close()
    assert type(caught.value) is BrokerHTTPError
    assert caught.value.status_code == 503
    assert events == [("error", 503), ("log", 503)]
    _assert_non_trade_http_attempt(client, reply, "query", secrets)
    assert_no_sensitive_logs(caplog.records, list(secrets.values()))


@pytest.mark.parametrize("kind", ["broker", "value", "base"])
def test_legacy_core_http_handler_failure_remains_original(monkeypatch, caplog, kind):
    caplog.set_level(logging.DEBUG)
    session = Mock(post=Mock(return_value=response(status=503)))
    token = SYNTHETIC
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", token)
    original = {"broker": BrokerHTTPError(401), "value": ValueError(), "base": HandlerAbortError()}[kind]
    message, note = "P3_R3_FAKE_LEGACY_MESSAGE", "P3_R3_FAKE_LEGACY_NOTE"
    original.args = (message,)
    original.add_note(note)

    class BrokenHandler(logging.Handler):
        def emit(self, record):
            raise original

    handler = BrokenHandler()
    core.logger.addHandler(handler)
    try:
        with pytest.raises(type(original)) as caught:
            core.query_orders()
    finally:
        core.logger.removeHandler(handler)
        handler.close()
    assert caught.value is original
    assert core.session is session
    assert core._em_validate_key == token
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["query_orders"] + token,)
    session.get.assert_not_called()
    assert_no_sensitive_logs(caplog.records, [token, message, note])
