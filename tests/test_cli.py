import os
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import pytest

HELPER = Path(__file__).with_name("_offline.py")


def run_cli(*args):
    code = (
        "import runpy,sys; runpy.run_path(sys.argv.pop(1))['install'](); sys.argv[0]='emtl'; runpy.run_module('emtl',run_name='__main__')"
    )
    env = {key: value for key, value in os.environ.items() if key not in ("EM_USERNAME", "EM_PASSWORD")}
    return subprocess.run([sys.executable, "-c", code, str(HELPER), *args], env=env, capture_output=True, text=True, check=False)


def test_cli():
    result = run_cli("-u=P0_FAKE_USER", "-p=P0_FAKE_PASSWORD")
    assert result.returncode == 0
    assert result.stdout == ""
    assert "P0_FAKE_USER" not in result.stderr
    assert "P0_FAKE_PASSWORD" not in result.stderr


def test_console_entry_point():
    entries = {entry.name: entry.value for entry in distribution("emtl").entry_points if entry.group == "console_scripts"}
    assert entries["emt"] == "emtl.cli:run"


def test_installed_console_script():
    script = Path(sys.executable).parent / "emt"
    assert script.is_file()
    code = (
        "import runpy,sys; runpy.run_path(sys.argv.pop(1))['install'](); sys.argv.pop(0); runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    env = {key: value for key, value in os.environ.items() if key not in ("EM_USERNAME", "EM_PASSWORD")}
    result = subprocess.run(
        [sys.executable, "-c", code, str(HELPER), str(script), "-u=P0_FAKE_USER", "-p=P0_FAKE_PASSWORD"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "P0_FAKE_USER" not in result.stderr
    assert "P0_FAKE_PASSWORD" not in result.stderr


@pytest.mark.parametrize(("args", "code"), [(("--help",), 0), (("-b", "x", "-s", "x"), 2), (("-q", "invalid"), 2)])
def test_cli_arguments(args, code):
    assert run_cli(*args).returncode == code
