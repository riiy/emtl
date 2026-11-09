"""Prepare dependencies, then run both installed artifacts in network=none."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke(artifacts, version, output):
    output.mkdir(parents=True, exist_ok=True)
    records = []
    name = "emtl-package-" + uuid.uuid4().hex
    created = False

    def command(args, label, *, check=True):
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("EM_") and key not in ("NETRC", "SSH_AUTH_SOCK", "SSH_AGENT_PID")
        }
        try:
            result = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1800, check=False)
            text, code = result.stdout, result.returncode
        except subprocess.TimeoutExpired:
            text, code = "command timed out\n", 124
        except OSError:
            text, code = "command unavailable\n", 127
        (output / f"{label}.log").write_text(text)
        records.append({"args": args, "exit_code": code, "log": f"{label}.log"})
        (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
        if check and code:
            raise RuntimeError(f"package smoke {label} failed ({code})")
        return text, code

    with tempfile.TemporaryDirectory(prefix="emtl-package-") as directory:
        context = Path(directory)
        shutil.copytree(artifacts, context / "artifacts")
        (context / "wheelhouse").mkdir()
        for file in ("package_smoke.py", "check_offline_network.py"):
            shutil.copyfile(ROOT / "ci" / file, context / file)
        command(["docker", "build", "-f", str(ROOT / "ci/package-smoke.Dockerfile"), "-t", name, str(context)], "build")
        command(["docker", "image", "inspect", name], "image")
        failed = False
        try:
            # Cleanup must also be attempted when create fails after daemon-side
            # creation but before a successful client response.
            created = True
            command(["docker", "create", "--name", name, "--network", "none", "-e", f"EXPECTED_VERSION={version}", name], "create")
            mode, _ = command(["docker", "inspect", "--format", "{{.HostConfig.NetworkMode}}", name], "network-mode")
            if mode.strip() != "none":
                raise RuntimeError("package smoke requires NetworkMode=none")
            command(["docker", "start", "--attach", name], "start")
            state, _ = command(["docker", "inspect", "--format", "{{.State.ExitCode}}", name], "exit-code")
            if state.strip() != "0":
                raise RuntimeError("package smoke container failed")
        except BaseException:
            failed = True
            raise
        finally:
            if created:
                _, log_status = command(["docker", "logs", name], "container", check=False)
                _, cleanup_status = command(["docker", "rm", "-f", name], "cleanup", check=False)
                if not failed and (log_status or cleanup_status):
                    raise RuntimeError("package smoke evidence/cleanup failed")
    print("both installed artifacts passed in NetworkMode=none")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("expected_version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run_smoke(args.artifacts, args.expected_version, args.output)


if __name__ == "__main__":
    main()
