"""Offline checks for the actual Docker context and workflow failure handling."""

import fnmatch
import json
import os
import runpy
import shlex
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def workflow_script():
    content = (ROOT / ".github/workflows/offline-tests.yml").read_text()
    block = content.split("      - name: Run complete tests without external network\n", 1)[1]
    return textwrap.dedent(block.split("        run: |\n", 1)[1].split("      - uses:", 1)[0])


def test_docker_copy_sources_and_coverage_config_are_not_ignored():
    # Our dockerignore has only simple positive patterns. This deliberately
    # checks those patterns, not a claim to implement Docker's full matcher.
    patterns = [line for line in (ROOT / ".dockerignore").read_text().splitlines() if line and not line.startswith("#")]
    assert all(not pattern.startswith("!") for pattern in patterns)
    for line in (ROOT / "ci/offline.Dockerfile").read_text().splitlines():
        if line.startswith("COPY "):
            for source in shlex.split(line)[1:-1]:
                source = source.rstrip("/")
                assert (ROOT / source).exists(), source
                assert not any(fnmatch.fnmatchcase(source, pattern) for pattern in patterns), source
    assert not any(fnmatch.fnmatchcase(".coveragerc", pattern) for pattern in patterns)
    for result in (".coverage", ".coverage.fake.123"):
        assert any(fnmatch.fnmatchcase(result, pattern) for pattern in patterns)


@pytest.mark.parametrize(
    ("start", "state", "tee", "copy", "cleanup", "mode", "expected"),
    [
        (0, 0, 0, 0, 0, "none", 0),
        (17, 0, 0, 0, 29, "none", 17),
        (17, 23, 31, 9, 29, "none", 17),
        (0, 23, 0, 0, 0, "none", 23),
        (0, 0, 31, 0, 0, "none", 31),
        (0, 0, 0, 9, 0, "none", 9),
        (0, 0, 0, 0, 29, "none", 29),
        (0, 0, 0, 0, 0, "bridge", 1),
    ],
)
def test_workflow_preserves_failure_and_always_collects(tmp_path, start, state, tee, copy, cleanup, mode, expected):
    # Shell functions ensure no Docker daemon or network is ever contacted.
    # Execute the workflow's exact run block under Actions' bash -e/pipefail.
    stubs = r"""
docker() {
  printf '%s\n' "$*" >> "$CALLS"
  case "$1" in
    image|create) echo fake; return 0 ;;
    inspect)
      if [[ "$*" == *NetworkMode* ]]; then echo "$MODE"; else echo "$STATE"; fi ;;
    start) echo "synthetic container output"; return "$START" ;;
    logs) echo "synthetic retained logs" ;;
    cp)
      if [ "$COPY" -ne 0 ]; then return "$COPY"; fi
      for file in junit.xml coverage.xml coverage.json tox-result.json versions.json commands.json; do
        echo fake > "dist/p1-offline/$file"
      done ;;
    rm) return "$CLEANUP" ;;
    *) return 99 ;;
  esac
}
tee() {
  if [[ "$*" == *container.log* ]] && [ "$TEE" -ne 0 ]; then
    cat > /dev/null; return "$TEE"
  else
    command tee "$@"
  fi
}
"""
    env = {key: value for key, value in os.environ.items() if not key.startswith("EM_")}
    env.update(
        {
            "CALLS": str(tmp_path / "calls.txt"),
            "START": str(start),
            "STATE": str(state),
            "TEE": str(tee),
            "COPY": str(copy),
            "CLEANUP": str(cleanup),
            "MODE": mode,
            "GITHUB_RUN_ID": "fake",
            "GITHUB_RUN_ATTEMPT": "1",
        }
    )
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", stubs + workflow_script()],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    calls = (tmp_path / "calls.txt").read_text().splitlines()
    assert any(line.startswith("logs ") for line in calls)
    assert any(line.startswith("cp ") for line in calls)
    assert any(line.startswith("rm -f ") for line in calls)
    out = tmp_path / "dist/p1-offline"
    assert "synthetic retained logs" in (out / "docker.log").read_text()
    assert (out / "host-status.txt").exists()


@pytest.mark.parametrize("code", [0, 17, 124])
def test_container_driver_records_and_propagates_command_status(monkeypatch, tmp_path, code):
    run = runpy.run_path(str(ROOT / "ci/run_offline_tests.py"))["run"]
    monkeypatch.setitem(run.__globals__, "OUT", tmp_path)

    def execute(args, **kwargs):
        kwargs["stdout"].write("P1_FAKE_COMMAND_OUTPUT\n")
        if code == 124:
            raise subprocess.TimeoutExpired(args, 600)
        return subprocess.CompletedProcess(args, code)

    monkeypatch.setattr(subprocess, "run", execute)
    if code:
        with pytest.raises(SystemExit) as caught:
            run(["fake-command"], cwd=tmp_path)
        assert caught.value.code == code
    else:
        assert run(["fake-command"], cwd=tmp_path) == "P1_FAKE_COMMAND_OUTPUT\n"
    record = json.loads((tmp_path / "commands.json").read_text())[0]
    assert record == {"args": ["fake-command"], "cwd": str(tmp_path), "exit_code": code, "log": "command-00.log"}
    assert "P1_FAKE_COMMAND_OUTPUT" in (tmp_path / record["log"]).read_text()
