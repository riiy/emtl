import logging
import os
import subprocess
import sys
from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl import core
from emtl.cli import run
from emtl.const import _base_headers
from emtl.const import _urls
from tests.helpers import OFFLINE_HELPER as HELPER
from tests.helpers import assert_no_sensitive_logs
from tests.helpers import response


def test_no_sensitive_log_records(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    sentinel = "P0_FAKE_SECRET"
    session = Mock()
    session.post.return_value = response({"nested": sentinel})
    session.get.return_value = response(text=f'id="em_validatekey" type="hidden" value="{sentinel}"')
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "get", Mock(return_value=response(text="P0_FAKE_IMAGE")))
    monkeypatch.setattr(core, "ocr", Mock(classification=Mock(return_value="1234")))
    monkeypatch.setattr(core, "emt_trade_encrypt", lambda value: sentinel)
    assert core.login(sentinel, sentinel) == sentinel
    core.query_orders()
    core.create_order(sentinel, "B", "SA", 1.0, 100)
    session.post.return_value = response(text=sentinel)
    core.cancel_order(sentinel)
    with pytest.raises(RuntimeError, match="No active exception"):
        core._check_resp(response(text=sentinel, status=500))
    session.post.return_value = response({})
    session.post.return_value.json = Mock(side_effect=KeyError(sentinel))
    assert core.login(sentinel, sentinel) is None
    for record in caplog.records:
        assert sentinel not in str(record.msg)
        assert sentinel not in str(record.args)
        assert sentinel not in record.getMessage()
        assert not record.exc_info


@pytest.mark.parametrize("configured", [False, True])
def test_import_does_not_reconfigure_root(configured):
    script = """
import logging, runpy, sys
runpy.run_path(sys.argv[1])['install']()
root = logging.getLogger()
class Handler(logging.Handler):
    def __init__(self):
        super().__init__(); self.was_closed = False; self.records = []
    def emit(self, record): self.records.append(record)
    def close(self): self.was_closed = True; super().close()
h = Handler(); fmt = logging.Formatter('%(message)s'); h.setFormatter(fmt)
configured = sys.argv[2] == 'True'
if configured:
    root.handlers[:] = [h]; root.setLevel(logging.DEBUG)
before = (root.level, list(root.handlers), list(root.filters), logging.root.manager.disable)
import emtl, emtl.cli
from emtl.utils import get_logger
assert get_logger('host.test') is get_logger('host.test')
get_logger('host.test').warning('safe event')
assert before == (root.level, list(root.handlers), list(root.filters), logging.root.manager.disable)
assert h.formatter is fmt and not h.was_closed
if configured:
    assert len([r for r in h.records if r.name == 'host.test']) == 1
"""
    env = {key: value for key, value in os.environ.items() if key not in ("EM_USERNAME", "EM_PASSWORD")}
    result = subprocess.run(
        [sys.executable, "-c", script, str(HELPER), str(configured)], env=env, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_cli_does_not_log_credentials(caplog, capsys):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(SystemExit) as exit_info:
        run(["-u=P0_FAKE_USER", "-p=P0_FAKE_PASSWORD"])
    assert exit_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "P0_FAKE_USER" not in captured.err
    assert "P0_FAKE_PASSWORD" not in captured.err
    assert "P0_FAKE_USER" not in caplog.text
    assert "P0_FAKE_PASSWORD" not in caplog.text


def test_captcha_invalid_ocr_recovers_without_leaking(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    invalid_code = "P0_FAKE_OCR_SECRET"
    first = response(text="P0_FAKE_IMAGE_ONE")
    second = response(text="P0_FAKE_IMAGE_TWO")
    http_get = Mock(side_effect=[first, second])
    classification = Mock(side_effect=[invalid_code, "1234"])
    random_value = Mock(side_effect=[0.25, 0.75])
    monkeypatch.setattr(core, "get", http_get)
    monkeypatch.setattr(core, "ocr", Mock(classification=classification))
    monkeypatch.setattr(core, "SystemRandom", Mock(return_value=Mock(random=random_value)))

    assert core._get_captcha_code() == (0.75, 1234)
    assert random_value.call_count == 2
    assert http_get.call_count == 2
    assert classification.call_count == 2
    assert [call.args for call in classification.call_args_list] == [(first.content,), (second.content,)]
    assert [call.args for call in http_get.call_args_list] == [(_urls["yzm"] + "0.25",), (_urls["yzm"] + "0.75",)]
    for call in http_get.call_args_list:
        assert call.kwargs == {"headers": _base_headers, "timeout": 60}
    records = [record for record in caplog.records if record.name == "emtl.core"]
    assert [record.getMessage() for record in records] == ["captcha recognition failed"]
    for record in records:
        assert invalid_code not in str(record.msg)
        assert invalid_code not in str(record.args)
        assert not record.exc_info


@pytest.mark.parametrize("status", [200, 500])
def test_url_cookie_and_response_secrets_are_not_logged(monkeypatch, caplog, status):
    caplog.set_level(logging.DEBUG)
    secrets = ["P0_FAKE_URL_TOKEN", "P0_FAKE_COOKIE", "P0_FAKE_AUTHORIZATION", "P0_FAKE_BODY"]
    result = response({"nested": {"sensitive": secrets[3]}}, status=status)
    result.url = "https://example.invalid/query?validatekey=" + secrets[0]
    result.headers["Set-Cookie"] = "session=" + secrets[1]
    result.cookies.set("session", secrets[1])
    session = Mock()
    session.cookies = result.cookies
    session.headers = {"Cookie": "session=" + secrets[1], "Authorization": secrets[2]}
    session.post.return_value = result
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", secrets[0])
    if status == 200:
        assert core.query_orders() == {"nested": {"sensitive": secrets[3]}}
    else:
        with pytest.raises(RuntimeError, match="No active exception"):
            core.query_orders()
    for record in caplog.records:
        for secret in secrets:
            assert secret not in record.getMessage()
            assert secret not in str(record.msg)
            assert secret not in str(record.args)
        assert not record.exc_info


@pytest.mark.parametrize("operation", ["query", "create", "cancel"])
def test_transport_exception_secret_is_not_logged(monkeypatch, caplog, operation):
    caplog.set_level(logging.DEBUG)
    secret = "P1_FAKE_EXCEPTION_" + "SECRET"
    error = requests.Timeout(secret)
    session = Mock(post=Mock(side_effect=error))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    calls = {
        "query": lambda: core.query_orders(),
        "create": lambda: core.create_order("P1_FAKE", "B", "SA", 1, 100),
        "cancel": lambda: core.cancel_order("P1_FAKE"),
    }
    with pytest.raises(requests.Timeout) as caught:
        calls[operation]()
    assert caught.value is error
    session.post.assert_called_once()
    for record in caplog.records:
        if record.name.startswith("emtl"):
            for field in (record.msg, record.args, record.getMessage(), record.exc_info, record.exc_text, record.stack_info):
                assert secret not in str(field)


@pytest.mark.parametrize("operation", ["create", "cancel"])
def test_response_processing_failure_does_not_log_secrets(monkeypatch, caplog, operation):
    caplog.set_level(logging.DEBUG)
    sentinels = ["P1_FAKE_REQUEST_BODY", "P1_FAKE_REPLY_BODY", "P1_FAKE_PROCESSING_EXCEPTION", "P1_FAKE_VALIDATEKEY"]
    error = ValueError(sentinels[2])
    reply = response({"echo": sentinels[1]})
    reply.url = "https://example.invalid/?validatekey=" + sentinels[3]
    if operation == "create":
        reply.json = Mock(side_effect=[{"echo": sentinels[1]}, error])
    else:
        monkeypatch.setattr(type(reply), "text", PropertyMock(side_effect=error))

    def invoke():
        if operation == "create":
            return core.create_order(sentinels[0], "S", "SA", 1.0, 100)
        return core.cancel_order(sentinels[0])

    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", sentinels[3])
    with pytest.raises(ValueError, match="P1_FAKE_PROCESSING_EXCEPTION") as caught:
        invoke()
    assert caught.value is error
    session.post.assert_called_once()
    assert_no_sensitive_logs(caplog.records, sentinels)
