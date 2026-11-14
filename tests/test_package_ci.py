"""Exercise the package driver's actual failure handling without Docker/network."""

import json
import runpy
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("failure", [None, "build", "create", "network", "start", "state", "logs", "rm", "timeout"])
def test_package_driver_failure_evidence_and_cleanup(monkeypatch, tmp_path, failure):
    run = runpy.run_path(str(ROOT / "ci/run_package_smoke.py"))["run_smoke"]
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "synthetic.whl").write_bytes(b"not executed")
    calls = []

    def fake(args, **kwargs):
        calls.append(args)
        operation = args[1]
        if operation == "start" and failure == "timeout":
            raise subprocess.TimeoutExpired(args, 1800)
        text = "synthetic output\n"
        if operation == "inspect":
            if "NetworkMode" in args[3]:
                text = "bridge\n" if failure == "network" else "none\n"
            else:
                text = "7\n" if failure == "state" else "0\n"
        return subprocess.CompletedProcess(args, 7 if operation == failure else 0, text)

    monkeypatch.setattr(subprocess, "run", fake)
    if failure is None:
        run(artifacts, "0.3.0", tmp_path / "evidence")
    else:
        with pytest.raises(RuntimeError, match="package smoke"):
            run(artifacts, "0.3.0", tmp_path / "evidence")
    if failure != "build":
        assert any(args[1] == "logs" for args in calls)
        assert any(args[1] == "rm" for args in calls)
    else:
        assert not any(args[1] == "create" for args in calls)
    records = json.loads((tmp_path / "evidence/commands.json").read_text())
    assert len(records) == len(calls)
    assert all((tmp_path / "evidence" / record["log"]).exists() for record in records)
    for args in calls:
        if args[1] == "create":
            assert args[args.index("--network") + 1] == "none"


def test_package_driver_preserves_start_failure_over_cleanup_failure(monkeypatch, tmp_path):
    run = runpy.run_path(str(ROOT / "ci/run_package_smoke.py"))["run_smoke"]
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    def fake(args, **kwargs):
        text = "none\n" if args[1] == "inspect" else "synthetic\n"
        return subprocess.CompletedProcess(args, 7 if args[1] in ("start", "rm") else 0, text)

    monkeypatch.setattr(subprocess, "run", fake)
    with pytest.raises(RuntimeError, match="start failed"):
        run(artifacts, "0.3.0", tmp_path / "evidence")
