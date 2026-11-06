"""Run preinstalled tox and entry-point checks in an isolated container."""

import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist/p1-offline"
COMMANDS = []


def run(args, *, cwd=ROOT, env=None):
    print("RUN", " ".join(str(arg) for arg in args), flush=True)
    log = OUT / f"command-{len(COMMANDS):02d}.log"
    with log.open("w", encoding="utf-8") as output:
        try:
            result = subprocess.run(args, cwd=cwd, env=env, timeout=600, stdout=output, stderr=subprocess.STDOUT, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
            output.write("command timed out\n")
    text = log.read_text(encoding="utf-8")
    print(text, end="", flush=True)
    print("EXIT", code, flush=True)
    COMMANDS.append({"args": [str(arg) for arg in args], "cwd": str(cwd), "exit_code": code, "log": log.name})
    (OUT / "commands.json").write_text(json.dumps(COMMANDS, indent=2), encoding="utf-8")
    if code:
        raise SystemExit(code if code > 0 else 128 - code)
    return text


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "ci/check_offline_network.py"])
    python = str(ROOT / ".tox/py311-cover/bin/python")
    versions = json.loads(
        run(
            [
                python,
                "-c",
                (
                    "import json,platform; from importlib.metadata import version; "
                    "print(json.dumps(dict(python=platform.python_version(), "
                    "packages={name:version(name) for name in ('pytest','pytest-cov','coverage')})))"
                ),
            ]
        )
    )
    versions["packages"]["tox"] = version("tox")
    (OUT / "versions.json").write_text(json.dumps(versions, indent=2), encoding="utf-8")
    synthetic = {
        key: "P1_FAKE_VALUE"
        for key in (
            "EM_USERNAME",
            "EM_PASSWORD",
            "EM_P1_SENTINEL",
            "P0_FAKE_ACCOUNT_CREDENTIAL",
            "P1_FAKE_ACCOUNT_CREDENTIAL",
            "NETRC",
            "SSH_AUTH_SOCK",
            "SSH_AGENT_PID",
        )
    }
    (OUT / "synthetic-environment.json").write_text(json.dumps(synthetic, indent=2), encoding="utf-8")
    env = dict(os.environ, **synthetic, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    run(
        [
            sys.executable,
            "-m",
            "tox",
            "-e",
            "py311-cover",
            "--skip-pkg-install",
            "-v",
            "--result-json",
            str(OUT / "tox-result.json"),
            "--",
            "python",
            "-m",
            "pytest",
            "--cov",
            "--cov-report=term-missing",
            f"--cov-report=xml:{OUT / 'coverage.xml'}",
            f"--cov-report=json:{OUT / 'coverage.json'}",
            f"--junitxml={OUT / 'junit.xml'}",
            "-vv",
        ],
        env=env,
    )
    priority = ["test_orders.py", "test_auth.py", "test_logging_safety.py", "test_core.py"]
    remaining = sorted(path.name for path in (ROOT / "tests").glob("test_*.py") if path.name not in priority)
    run(
        [
            python,
            "-m",
            "pytest",
            "-vv",
            f"--junitxml={OUT / 'outside-junit.xml'}",
            *[str(ROOT / "tests" / name) for name in priority + remaining],
        ],
        cwd="/tmp",
        env=env,
    )
    run([python, "-m", "pytest", "tests/", "-q", f"--junitxml={OUT / 'explicit-junit.xml'}"], env=env)
    for name in ("coverage.xml", "coverage.json", "junit.xml", "outside-junit.xml", "explicit-junit.xml", "tox-result.json"):
        if not (OUT / name).is_file() or (OUT / name).stat().st_size == 0:
            raise SystemExit("required offline report missing")


if __name__ == "__main__":
    main()
