import logging
from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import call

import pytest
import requests

from emtl import core
from emtl.const import _base_headers
from emtl.const import _urls
from tests.helpers import assert_no_sensitive_logs
from tests.helpers import response


@pytest.mark.parametrize("code", ["", None, False, 0])
def test_invalid_ocr_retries_before_auth_post(monkeypatch, fake_captcha, code):
    fake_captcha.classification.side_effect = [code, "0019"]
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "P1_FAKE_ENCRYPTED")
    session = Mock()
    session.post.return_value = response({"Status": -1})
    session.get.return_value = response(text="no token")
    monkeypatch.setattr(core, "session", session)
    assert core.login("P1_FAKE_USER", "P1_FAKE_PASSWORD") is None
    assert session.post.call_args.kwargs["data"]["identifyCode"] == "0019"
    assert core.get.call_count == 2
    assert fake_captcha.classification.call_count == 2
    session.post.assert_called_once()
    session.get.assert_called_once()


@pytest.mark.parametrize(("user", "password", "expected"), [("", "", ("", "")), ("  ", "  ", ("", ""))])
def test_empty_credentials_and_whitespace(monkeypatch, fake_captcha, user, password, expected):
    if user:
        monkeypatch.setenv("EM_USERNAME", "P1_FAKE_ENV_USER")
        monkeypatch.setenv("EM_PASSWORD", "P1_FAKE_ENV_PASSWORD")
    encrypt = Mock(return_value="P1_FAKE_ENCRYPTED")
    monkeypatch.setattr(core, "emt_trade_encrypt", encrypt)
    session = Mock(post=Mock(return_value=response({})), get=Mock(return_value=response(text="no token")))
    monkeypatch.setattr(core, "session", session)
    assert core.login(user, password) is None
    assert session.post.call_args.kwargs["data"]["userId"] == expected[0]
    encrypt.assert_called_once_with(expected[1])


@pytest.mark.parametrize(
    ("html", "expected", "state"),
    [
        ("missing", None, "OLD"),
        ('id="em_validatekey" type="hidden" value="   "', "", ""),
        ('id="em_validatekey" type="hidden" value=" first " id="em_validatekey" type="hidden" value="second"', "first", "first"),
    ],
)
def test_rejected_login_still_extracts_token(monkeypatch, fake_captcha, html, expected, state):
    monkeypatch.setattr(core, "_em_validate_key", "OLD")
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "fake")
    session = Mock(post=Mock(return_value=response({"Status": -1})), get=Mock(return_value=response(text=html)))
    monkeypatch.setattr(core, "session", session)
    assert core.login("user", "password") == expected
    assert core._em_validate_key == state
    session.post.assert_called_once()
    session.get.assert_called_once()


@pytest.mark.parametrize("error", [requests.Timeout("P1_FAKE_ERROR"), requests.ConnectionError("P1_FAKE_ERROR")])
def test_token_fetch_error_propagates(monkeypatch, fake_captcha, error):
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "fake")
    session = Mock(post=Mock(return_value=response({})), get=Mock(side_effect=error))
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(type(error)) as caught:
        core.login("user", "password")
    assert caught.value is error
    session.post.assert_called_once()
    session.get.assert_called_once()


def test_failed_auto_login_does_not_post_query(monkeypatch, fake_captcha):
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "fake")
    session = Mock(post=Mock(return_value=response({})), get=Mock(return_value=response(text="no token")))
    monkeypatch.setattr(core, "session", session)
    with pytest.raises(TypeError):
        core.query_orders()
    session.post.assert_called_once()


@pytest.mark.parametrize("stage", ["http_status", "http_timeout", "ocr"])
def test_captcha_failure_prevents_authentication_post(monkeypatch, fake_captcha, stage):
    session = Mock()
    monkeypatch.setattr(core, "session", session)
    if stage == "http_status":
        core.get.return_value = response(status=500)
        error_type = RuntimeError
    elif stage == "http_timeout":
        core.get.side_effect = requests.Timeout("P1_FAKE_TIMEOUT")
        error_type = requests.Timeout
    else:
        fake_captcha.classification.side_effect = ValueError("P1_FAKE_OCR")
        error_type = ValueError
    with pytest.raises(error_type):
        core.login("P1_FAKE_USER", "P1_FAKE_PASSWORD")
    core.get.assert_called_once()
    session.post.assert_not_called()


def test_real_auto_login_then_query(monkeypatch, fake_captcha):
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: "P1_FAKE_ENCRYPTED")
    session = Mock()
    session.post.side_effect = [response({}), response(["P1_FAKE_RESULT"])]
    session.get.return_value = response(text='id="em_validatekey" type="hidden" value="P1_FAKE_TOKEN"')
    monkeypatch.setattr(core, "session", session)
    assert core.query_orders() == ["P1_FAKE_RESULT"]
    assert session.post.call_count == 2
    assert session.post.call_args_list[0].args == (core._urls["login"],)
    assert session.post.call_args_list[1].args == (core._urls["query_orders"] + "P1_FAKE_TOKEN",)
    session.get.assert_called_once()


def test_explicit_credentials_override_environment_and_preserve_request(monkeypatch, fake_captcha):
    monkeypatch.setenv("EM_USERNAME", "P1_FAKE_ENV_USER")
    monkeypatch.setenv("EM_PASSWORD", "P1_FAKE_ENV_PASSWORD")
    encrypt = Mock(return_value="P1_FAKE_ENCRYPTED")
    monkeypatch.setattr(core, "emt_trade_encrypt", encrypt)
    session = Mock(
        post=Mock(return_value=response({"Status": 0})),
        get=Mock(return_value=response(text='id="em_validatekey" type="hidden" value=" P1_FAKE_TOKEN "')),
    )
    monkeypatch.setattr(core, "session", session)
    before = _base_headers.copy()
    assert core.login(" P1_FAKE_USER ", " P1_FAKE_PASSWORD ", duration=7) == "P1_FAKE_TOKEN"
    encrypt.assert_called_once_with("P1_FAKE_PASSWORD")
    headers = dict(
        before,
        **{
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert session.mock_calls == [
        call.post(
            _urls["login"],
            headers=headers,
            data={
                "userId": "P1_FAKE_USER",
                "password": "P1_FAKE_ENCRYPTED",
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
    core.get.assert_called_once()
    fake_captcha.classification.assert_called_once()


@pytest.mark.parametrize(
    "stage", ["login_http", "login_timeout", "login_connection", "token_http", "token_text_keyerror", "token_text_valueerror", "login_json"]
)
def test_auth_failures_preserve_state_and_safe_logs(monkeypatch, fake_captcha, caplog, stage):
    caplog.set_level(logging.DEBUG)
    sentinels = [
        "P1_FAKE_USER",
        "P1_FAKE_PASSWORD",
        "P1_FAKE_ENCRYPTED",
        "P1_FAKE_TOKEN",
        "P1_FAKE_COOKIE",
        "P1_FAKE_AUTHORIZATION",
        "P1_FAKE_RESPONSE_BODY",
        "P1_FAKE_EXCEPTION",
    ]
    monkeypatch.setattr(core, "_em_validate_key", sentinels[3])
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: sentinels[2])
    login_reply = response({"echo": sentinels[6]})
    token_reply = response(text=sentinels[6])
    for reply in (login_reply, token_reply):
        reply.url = "https://example.invalid/?validatekey=" + sentinels[3]
        reply.headers["Set-Cookie"] = sentinels[4]
    session = Mock(post=Mock(return_value=login_reply), get=Mock(return_value=token_reply))
    session.headers = {"Cookie": sentinels[4], "Authorization": sentinels[5]}
    monkeypatch.setattr(core, "session", session)
    error = None
    if stage in ("login_http", "token_http"):
        (login_reply if stage == "login_http" else token_reply).status_code = 503
        error_type = RuntimeError
    elif stage in ("login_timeout", "login_connection"):
        error = (requests.Timeout if stage == "login_timeout" else requests.ConnectionError)(sentinels[7])
        session.post.side_effect = error
        error_type = type(error)
    elif stage == "login_json":
        login_reply._content = sentinels[6].encode()
        error_type = requests.exceptions.JSONDecodeError
    else:
        error = (KeyError if stage == "token_text_keyerror" else ValueError)(sentinels[7])
        monkeypatch.setattr(type(token_reply), "text", PropertyMock(side_effect=error))
        error_type = type(error)
    if stage == "token_text_keyerror":
        assert core.login(sentinels[0], sentinels[1]) is None
    else:
        with pytest.raises(error_type) as caught:
            core.login(sentinels[0], sentinels[1])
        if error is not None:
            assert caught.value is error
    session.post.assert_called_once()
    assert session.get.call_count == (1 if stage.startswith("token_") else 0)
    assert core._em_validate_key == sentinels[3]
    assert_no_sensitive_logs(caplog.records, sentinels)
