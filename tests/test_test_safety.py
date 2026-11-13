import configparser
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import requests

from emtl import core

ROOT = Path(__file__).resolve().parents[1]
COLLECTION_OCR = type(core.ocr).__name__
COLLECTION_CREDENTIALS_CLEARED = not any(os.environ.get(name) for name in ("EM_USERNAME", "EM_PASSWORD"))


def test_bootstrap_was_installed_before_collection():
    assert COLLECTION_OCR == "TinyCaptchaOCR"
    assert sys.modules["ddddocr"].DdddOcr.__name__ == "FakeOcr"
    assert requests.sessions.Session.request.__name__ == "blocked"
    assert COLLECTION_CREDENTIALS_CLEARED


def test_guards_precede_socket_transport(monkeypatch):
    called = []
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: called.append(True))
    with pytest.raises(RuntimeError, match="network disabled in tests"):
        requests.get("http://example.invalid/P0_FAKE_SECRET", timeout=1)
    assert not called


def test_socket_and_dns_are_blocked():
    with pytest.raises(RuntimeError, match=r"^network disabled in tests$"):
        socket.getaddrinfo("P0_FAKE_SECRET", 1)
    with socket.socket() as sock:
        assert sock.connect.__name__ == "blocked"
        with pytest.raises(RuntimeError, match=r"^network disabled in tests$"):
            sock.connect(("127.0.0.1", 1))


def test_captcha_transport_is_unconfigured():
    with pytest.raises(RuntimeError, match="unconfigured test HTTP"):
        core._get_captcha_code()


def test_ci_has_no_account_injection():
    workflows = list((ROOT / ".github/workflows").glob("*.yml"))
    assert workflows
    for path in workflows:
        content = path.read_text()
        assert "EM_USERNAME" not in content
        assert "EM_PASSWORD" not in content
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "tox.ini")
    for section in ("testenv", "testenv:bootstrap"):
        passenv = config[section]["passenv"]
        assert "*" not in passenv
        assert "EM_USERNAME" not in passenv
        assert "EM_PASSWORD" not in passenv
    assert "EM_USERNAME=" in config["testenv"]["setenv"]
    assert "EM_PASSWORD=" in config["testenv"]["setenv"]
    assert set(config["testenv"]["disallow_pass_env"].split()) == {"EM_*", "NETRC", "SSH_AUTH_SOCK", "SSH_AGENT_PID"}


def test_checkout_entry_from_outside_repository(tmp_path):
    env = {key: value for key, value in os.environ.items() if key not in ("EM_USERNAME", "EM_PASSWORD", "PYTEST_ADDOPTS")}
    env.update({"EM_USERNAME": "P0_FAKE_PARENT_USER", "EM_PASSWORD": "P0_FAKE_PARENT_PASSWORD"})
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(Path(__file__)),
            "-k",
            "bootstrap_was_installed_before_collection",
            "-q",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_no_unsafe_package_test_entry():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "pytest.ini")
    assert config["pytest"]["testpaths"].strip() == "tests"
    assert "--pyargs" not in config["pytest"]["addopts"]
    assert not (ROOT / "src/emtl/tests/__init__.py").exists()


def test_contract_download_target_exists():
    page = ROOT / "docs/reference/emtl.rst"
    target = page.parent / "../refactor/contracts/P0-public-api.md"
    assert target.is_file()
    assert "../refactor/contracts/P0-public-api.md" in page.read_text()


def test_new_client_unconfigured_http_is_guarded():
    from emtl import TradingClient

    client = TradingClient("P2_FAKE_USER", "P2_FAKE_PASSWORD")
    try:
        for operation in (client.login, lambda: client.get_last_price("FAKE", "SA")):
            with pytest.raises(RuntimeError, match="^network disabled in tests$"):
                operation()
        assert client._state == "FAILED"
        assert client._token == ""
        assert client._ocr is None
        assert requests.sessions.Session.request.__name__ == "blocked"
        assert requests.sessions.Session.send.__name__ == "blocked"
    finally:
        client.close()
