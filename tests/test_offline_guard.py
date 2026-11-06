"""Exercise guard lifecycle in a separate process with safe transport sentinels."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("existing_ocr", [False, True])
def test_guard_lifecycle_and_transport_sentinels(existing_ocr):
    helper = Path(__file__).with_name("_offline.py")
    script = r"""
import runpy, socket, sys, types
import requests

calls = []
def sentinel(*args, **kwargs):
    calls.append(True)
    raise RuntimeError("safe sentinel")

targets = [(requests.sessions.Session, n) for n in ("request", "send")]
targets += [(socket.socket, n) for n in ("connect", "connect_ex", "send", "sendall", "sendto", "sendmsg") if hasattr(socket.socket, n)]
targets += [(socket, n) for n in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo")]
for owner, name in targets:
    setattr(owner, name, sentinel)
original = types.ModuleType("ddddocr") if sys.argv[2] == "True" else None
if original is None:
    sys.modules.pop("ddddocr", None)
else:
    sys.modules["ddddocr"] = original
guard = runpy.run_path(sys.argv[1])
guard["restore"]()
for _ in range(2):
    guard["install"]()
    guard["install"]()
    for owner, name in targets:
        try:
            getattr(owner, name)()
        except RuntimeError as exc:
            assert str(exc) == "network disabled in tests"
        else:
            raise AssertionError(name)
    assert not calls
    assert sys.modules["ddddocr"].DdddOcr.__name__ == "FakeOcr"
    guard["restore"]()
    guard["restore"]()
    assert all(getattr(owner, name) is sentinel for owner, name in targets)
    assert sys.modules.get("ddddocr") is original
"""
    env = {key: value for key, value in os.environ.items() if key not in ("EM_USERNAME", "EM_PASSWORD")}
    result = subprocess.run(
        [sys.executable, "-c", script, str(helper), str(existing_ocr)], capture_output=True, text=True, env=env, timeout=30
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("parent_credentials", [False, True])
def test_root_conftest_initialization_and_unconfigure_restore(tmp_path, parent_credentials):
    script = r"""
import os, socket, sys, types
from pathlib import Path
import pytest, requests

root = Path(sys.argv[1])
names = ("EM_USERNAME", "EM_PASSWORD")
before_env = {name: os.environ.get(name) for name in names}
calls = []
def sentinel(*args, **kwargs):
    calls.append(True)
    raise RuntimeError("safe transport sentinel")

targets = [(requests.sessions.Session, n) for n in ("request", "send")]
targets += [(socket.socket, n) for n in ("connect", "connect_ex", "send", "sendall", "sendto", "sendmsg") if hasattr(socket.socket, n)]
targets += [(socket, n) for n in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo")]
for owner, name in targets:
    setattr(owner, name, sentinel)
before_functions = [(owner, name, getattr(owner, name)) for owner, name in targets]
original_ocr = types.ModuleType("ddddocr")
sys.modules["ddddocr"] = original_ocr

class Probe:
    checked = False
    def pytest_collection_modifyitems(self, session, config, items):
        assert all(name not in os.environ for name in names)
        from emtl import core
        assert sys.modules["ddddocr"].DdddOcr.__name__ == "FakeOcr"
        attempts = [
            lambda: requests.get("https://example.invalid/P1_FAKE", timeout=1),
            lambda: requests.post("https://example.invalid/P1_FAKE", data="P1_FAKE", timeout=1),
            lambda: requests.Session().send(requests.PreparedRequest()),
            lambda: core.get("https://example.invalid/P1_FAKE", timeout=1),
            lambda: socket.getaddrinfo("example.invalid", 9),
        ]
        with socket.socket() as sock:
            attempts.append(lambda: sock.connect(("127.0.0.1", 9)))
            for attempt in attempts:
                try:
                    attempt()
                except RuntimeError as exc:
                    assert str(exc) == "network disabled in tests"
                else:
                    raise AssertionError("guard did not reject operation")
        assert not calls
        self.checked = True

probe = Probe()
code = pytest.main(["-p", "no:cacheprovider", str(root / "tests/test_test_safety.py"),
                    "-k", "bootstrap_was_installed_before_collection", "-q"], plugins=[probe])
assert code == 0 and probe.checked
assert {name: os.environ.get(name) for name in names} == before_env
assert all(getattr(owner, name) is original for owner, name, original in before_functions)
assert sys.modules["ddddocr"] is original_ocr
assert not calls
# Restoration must expose only our safe sentinel, never real transport.
try:
    requests.get("https://example.invalid/P1_FAKE", timeout=1)
except RuntimeError as exc:
    assert str(exc) == "safe transport sentinel"
else:
    raise AssertionError("sentinel not restored")
assert calls == [True]
print("root conftest isolation and restoration verified")
"""
    root = Path(__file__).resolve().parents[1]
    env = {key: value for key, value in os.environ.items() if not key.startswith("EM_") and key != "PYTEST_ADDOPTS"}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    if parent_credentials:
        env.update({"EM_USERNAME": "P1_FAKE_PARENT_USER", "EM_PASSWORD": "P1_FAKE_PARENT_PASSWORD"})
    result = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "root conftest isolation and restoration verified" in result.stdout
