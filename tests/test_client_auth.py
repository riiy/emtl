from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import call

import pytest
import requests

from emtl import client as client_module
from emtl.const import _base_headers
from emtl.const import _urls
from emtl.errors import BrokerHTTPError
from tests.client_helpers import SYNTHETIC
from tests.client_helpers import ready
from tests.client_helpers import token_reply
from tests.helpers import response


@pytest.fixture(autouse=True)
def _auth_dependencies(monkeypatch):
    monkeypatch.setattr(client_module, "SystemRandom", Mock(return_value=Mock(random=Mock(return_value=0.5))))
    monkeypatch.setattr(client_module, "emt_trade_encrypt", Mock(return_value="P2_FAKE_ENCRYPTED"))


def configure_auth(client, payload=None, token=SYNTHETIC):
    client._session.get.side_effect = [response(text="P2_FAKE_IMAGE"), token_reply(token)]
    client._session.post.return_value = response({"Status": 0} if payload is None else payload)


def test_login_uses_bound_credentials_and_exact_request_chain(client_factory, monkeypatch):
    client = client_factory(" P2_FAKE_A ", " P2_FAKE_PASSWORD ")
    monkeypatch.setenv("EM_USERNAME", "P2_FAKE_OTHER")
    monkeypatch.setenv("EM_PASSWORD", "P2_FAKE_OTHER_PASSWORD")
    new_value = " P2_FAKE_NEW_TOKEN "
    configure_auth(client, token=new_value)
    before = _base_headers.copy()
    assert client.login(duration=7) == "P2_FAKE_NEW_TOKEN"
    client_module.emt_trade_encrypt.assert_called_once_with("P2_FAKE_PASSWORD")
    assert client._state == "READY"
    assert client._token == new_value.strip()
    assert client._session.mock_calls == [
        call.get(_urls["yzm"] + "0.5", headers=before, timeout=60),
        call.post(
            _urls["login"],
            headers=dict(
                before,
                **{
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            ),
            data={
                "userId": "P2_FAKE_A",
                "password": "P2_FAKE_ENCRYPTED",
                "randNumber": 0.5,
                "identifyCode": "1234",
                "duration": 7,
                "authCode": "",
                "type": "Z",
                "secInfo": "",
            },
        ),
        call.get("https://jywg.18.cn/Trade/Buy", headers=before),
    ]
    assert _base_headers == before
    for request in client._session.mock_calls:
        assert request.kwargs["headers"] is not _base_headers


@pytest.mark.parametrize("payload", [{"Status": -1}, {}, {"Status": True}, {"Status": False}, {"Status": "0"}, {"Status": 0.0}, [], None])
def test_insufficient_login_evidence_clears_old_state_and_blocks_business(client_factory, payload):
    client = ready(client_factory(), "P2_FAKE_OLD_TOKEN")
    client._session.cookies.set("old", "P2_FAKE_COOKIE")
    client._session.get.return_value = response(text="P2_FAKE_IMAGE")
    client._session.post.return_value = response(payload)
    assert client.login() is None
    assert client._token == ""
    assert client._state == "FAILED"
    assert not client._session.cookies
    assert client._session.get.call_count == 1  # captcha only, not token fetch
    client._session.post.assert_called_once()
    client._session.reset_mock()
    for operation in (client.query_orders, lambda: client.create_order("FAKE", "B", "SA", 1, 100), lambda: client.cancel_order("FAKE")):
        with pytest.raises(RuntimeError, match="^authentication required$"):
            operation()
    client._session.post.assert_not_called()
    client._session.get.assert_not_called()


@pytest.mark.parametrize("html", ["missing", 'id="em_validatekey" type="hidden" value="   "'])
def test_new_token_is_required_after_a_successful_login(client_factory, html):
    client = client_factory()
    configure_auth(client)
    assert client.login() == "P2_FAKE_TOKEN"
    session = client._session
    session.cookies.set("old", "P2_FAKE_COOKIE")
    session.get.side_effect = [response(text="P2_FAKE_IMAGE"), response(text=html)]
    assert client.login() is None
    assert client._token == ""
    assert client._state == "FAILED"
    assert not session.cookies
    recovered = "P2_FAKE_RECOVERED"
    configure_auth(client, token=recovered)
    assert client.login() == "P2_FAKE_RECOVERED"


@pytest.mark.parametrize(
    "stage",
    [
        "captcha_http",
        "captcha_timeout",
        "ocr",
        "encrypt",
        "login_http",
        "login_timeout",
        "login_connection",
        "json",
        "json_keyerror",
        "token_http",
        "token_timeout",
        "token_text",
        "token_keyerror",
    ],
)
def test_authentication_failure_invalidates_state_and_preserves_exception(client_factory, monkeypatch, stage):
    client = client_factory()
    configure_auth(client)
    assert client.login() == "P2_FAKE_TOKEN"
    session = client._session
    session.reset_mock()
    session.cookies.set("old", "P2_FAKE_COOKIE")
    captcha, login, token = response(text="P2_FAKE_IMAGE"), response({"Status": 0}), token_reply()
    session.get.side_effect = [captcha, token]
    session.post.return_value = login
    error = None
    expected = BrokerHTTPError
    if stage.endswith("http"):
        {"captcha_http": captcha, "login_http": login, "token_http": token}[stage].status_code = 503
    elif stage in {"captcha_timeout", "login_timeout", "login_connection", "token_timeout"}:
        error = (requests.ConnectionError if stage == "login_connection" else requests.Timeout)("P2_FAKE_ERROR")
        if stage == "captcha_timeout":
            session.get.side_effect = error
        elif stage == "token_timeout":
            session.get.side_effect = [captcha, error]
        else:
            session.post.side_effect = error
    else:
        error = (KeyError if stage in {"json_keyerror", "token_keyerror"} else ValueError)("P2_FAKE_ERROR")
        if stage == "ocr":
            client._ocr.classification.side_effect = error
        elif stage == "encrypt":
            client_module.emt_trade_encrypt.side_effect = error
        elif stage in {"json", "json_keyerror"}:
            login.json = Mock(side_effect=error)
        else:
            monkeypatch.setattr(type(token), "text", PropertyMock(side_effect=error))
    if error is not None:
        expected = type(error)
    with pytest.raises(expected) as caught:
        client.login()
    if error is not None:
        assert caught.value is error
    else:
        assert type(caught.value) is BrokerHTTPError
        assert caught.value.status_code == 503
    assert client._token == ""
    assert client._state == "FAILED"
    assert not session.cookies
    assert session.post.call_count == (0 if stage.startswith("captcha") or stage in {"ocr", "encrypt"} else 1)
    assert session.get.call_count == (2 if stage.startswith("token") else 1)


def test_failed_auto_login_posts_no_business_and_requires_explicit_recovery(client_factory):
    client = client_factory()
    configure_auth(client, payload={"Status": -1})
    with pytest.raises(RuntimeError, match="authentication required"):
        client.query_orders()
    assert client._session.post.call_args.args == (_urls["login"],)
    client._session.post.assert_called_once()
    with pytest.raises(RuntimeError, match="authentication required"):
        client.query_orders()
    client._session.post.assert_called_once()
    configure_auth(client)
    assert client.login() == "P2_FAKE_TOKEN"
    client._session.post.return_value = response(["P2_FAKE_RESULT"])
    assert client.query_orders() == ["P2_FAKE_RESULT"]


def test_auto_login_is_reentrant_and_cookies_belong_to_current_attempt(client_factory):
    client = client_factory()
    session = client._session
    session.cookies.set("old", "P2_FAKE_OLD_COOKIE")

    def get(url, **kwargs):
        if url.startswith(_urls["yzm"]):
            assert not session.cookies
            session.cookies.set("captcha", "P2_FAKE_NEW_COOKIE")
            return response(text="P2_FAKE_IMAGE")
        assert session.cookies.get("captcha") == "P2_FAKE_NEW_COOKIE"
        return token_reply()

    def post(url, **kwargs):
        assert session.cookies.get("captcha") == "P2_FAKE_NEW_COOKIE"
        return response({"Status": 0} if url == _urls["login"] else ["P2_FAKE_RESULT"])

    session.get.side_effect = get
    session.post.side_effect = post
    assert client.query_orders() == ["P2_FAKE_RESULT"]
    assert session.post.call_count == 2
    assert session.post.call_args_list[1].args == (_urls["query_orders"] + "P2_FAKE_TOKEN",)


@pytest.mark.parametrize("code", ["", None, False, 0])
def test_invalid_ocr_never_reaches_login_post(client_factory, code):
    ocr = Mock(classification=Mock(side_effect=[code, "0019"]))
    client = client_factory(ocr=ocr)
    client._session.get.side_effect = [response(text="invalid"), response(text="valid"), token_reply()]
    client._session.post.return_value = response({"Status": 0})
    assert client.login() == "P2_FAKE_TOKEN"
    assert client._session.post.call_args.kwargs["data"]["identifyCode"] == "0019"
    assert client._session.get.call_count == 3
    assert ocr.classification.call_count == 2
    client._session.post.assert_called_once()


def test_invalid_ocr_recovery_executes_real_captcha_chain(client_factory):
    ocr = Mock(classification=Mock(side_effect=["P2_FAKE_BAD_CODE", "1234"]))
    client = client_factory(ocr=ocr)
    client._session.get.side_effect = [response(text="one"), response(text="two"), token_reply()]
    client._session.post.return_value = response({"Status": 0})
    assert client.login() == "P2_FAKE_TOKEN"
    assert client._session.get.call_count == 3
    assert ocr.classification.call_args_list == [call(b"one"), call(b"two")]
    client._session.post.assert_called_once()


def test_primary_auth_error_is_not_masked_by_cookie_cleanup_error(client_factory, monkeypatch):
    client = client_factory()
    configure_auth(client)
    error = requests.Timeout("P2_FAKE_PRIMARY")
    client._session.post.side_effect = error
    clear = Mock(side_effect=[None, ValueError("P2_FAKE_CLEANUP"), None])
    monkeypatch.setattr(client._session.cookies, "clear", clear)
    with pytest.raises(requests.Timeout) as caught:
        client.login()
    assert caught.value is error
    assert client._state == "FAILED"
    assert not client._token


@pytest.mark.parametrize("previously_authenticated", [False, True], ids=["new", "previously_authenticated"])
@pytest.mark.parametrize("stage", ["auth_rejected", "token_missing", "auth_timeout", "token_connection_error"])
def test_failed_login_clears_cookies_created_during_http(client_factory, previously_authenticated, stage):
    client = client_factory()
    if previously_authenticated:
        configure_auth(client)
        assert client.login() == SYNTHETIC
        assert client._token == SYNTHETIC
    else:
        assert client._state == "NEW"
        assert client._token == ""
    session = client._session
    session.reset_mock(side_effect=True)
    jar = session.cookies
    jar.set("old", "P2_FAKE_OLD_COOKIE")
    writes = []
    error = None
    if stage == "auth_timeout":
        error = requests.Timeout("P2_FAKE_AUTH_TIMEOUT")
    elif stage == "token_connection_error":
        error = requests.ConnectionError("P2_FAKE_TOKEN_CONNECTION")

    def write_attempt_cookie(name):
        # The old jar/token must already be invalidated, but this new cookie
        # appears AFTER login's initial clear. Only failure cleanup removes it.
        assert jar.get("old") is None
        assert client._token == ""
        jar.set(name, "P2_FAKE_ATTEMPT_COOKIE")
        assert jar.get(name) == "P2_FAKE_ATTEMPT_COOKIE"
        writes.append(name)

    def post(url, **kwargs):
        assert url == _urls["login"]
        write_attempt_cookie("auth_attempt")
        if stage == "auth_timeout":
            raise error
        return response({"Status": -1 if stage == "auth_rejected" else 0})

    def get(url, **kwargs):
        if url.startswith(_urls["yzm"]):
            assert not jar
            return response(text="P2_FAKE_IMAGE")
        assert url == "https://jywg.18.cn/Trade/Buy"
        assert stage in {"token_missing", "token_connection_error"}
        assert jar.get("auth_attempt") == "P2_FAKE_ATTEMPT_COOKIE"
        write_attempt_cookie("token_attempt")
        if stage == "token_connection_error":
            raise error
        return response(text="P2_FAKE_NO_TOKEN_HTML")

    session.post.side_effect = post
    session.get.side_effect = get
    if error is None:
        assert client.login() is None
    else:
        with pytest.raises(type(error)) as caught:
            client.login()
        assert caught.value is error
    token_stage = stage.startswith("token_")
    assert writes == (["auth_attempt", "token_attempt"] if token_stage else ["auth_attempt"])
    assert client._token == ""
    assert client._state == "FAILED"
    assert client._session.cookies is jar
    assert not jar
    session.post.assert_called_once()
    assert session.get.call_count == (2 if token_stage else 1)

    # FAILED must not silently reauthenticate or send any business request.
    calls_after_failure = list(session.mock_calls)
    with pytest.raises(RuntimeError, match="^authentication required$"):
        client.query_orders()
    assert session.mock_calls == calls_after_failure
