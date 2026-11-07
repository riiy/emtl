import logging
from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl import client as client_module
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
            with pytest.raises(RuntimeError):
                client.query_orders()
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

            with pytest.raises(type(error)) as caught:
                invoke()
            assert caught.value is error
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
