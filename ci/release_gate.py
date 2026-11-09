"""Read-only, exact-SHA release gates. Never uploads or creates tags/releases."""

import argparse
import configparser
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from packaging.version import Version

REQUIRED_WORKFLOWS = {
    "github-actions.yml": {"check", "docs", "py311-cover (ubuntu)", "finish"},
    "offline-tests.yml": {"offline"},
    "packages.yml": {"package"},
}


def tag_version(tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", tag):
        raise ValueError("invalid release tag")
    version = tag[1:]
    if str(Version(version)) != version:
        raise ValueError("non-canonical release tag")
    return version


def publish_intent(event, ref, version, channel):
    if event != "workflow_dispatch" or ref != "refs/heads/master":
        raise ValueError("publishing requires manual dispatch from master")
    parsed = Version(version)
    if channel == "beta":
        if parsed.pre is None or parsed.pre[0] not in ("b", "rc"):
            raise ValueError("beta publishing requires a beta/rc version")
    elif channel != "stable" or parsed.is_prerelease:
        raise ValueError("stable publishing requires a stable version")


def check_remote(api, sha, *, publishing):
    for workflow, jobs in REQUIRED_WORKFLOWS.items():
        data = api(f"actions/workflows/{workflow}/runs?head_sha={sha}&event=push&branch=master&per_page=100")
        runs = [
            item
            for item in data["workflow_runs"]
            if item["head_sha"] == sha and item["head_branch"] == "master" and item["event"] == "push"
        ]
        if not runs or runs[0]["status"] != "completed" or runs[0]["conclusion"] != "success":
            raise ValueError("required exact-SHA master CI missing or unsuccessful")
        # API results are newest first; never fall back to a stale successful
        # job list from a different SHA or PR workflow.
        checks = api(f"actions/runs/{runs[0]['id']}/jobs?per_page=100")
        if checks["total_count"] != len(checks["jobs"]):
            raise ValueError("incomplete required job evidence")
        passed = {item["name"] for item in checks["jobs"] if item["status"] == "completed" and item["conclusion"] == "success"}
        if not jobs <= passed:
            raise ValueError("required CI job missing, skipped or unsuccessful")
    if publishing:
        environment = api("environments/pypi")
        if not any(rule["type"] == "required_reviewers" and rule.get("reviewers") for rule in environment["protection_rules"]):
            raise ValueError("pypi environment lacks active required reviewers")


def github_api(repository, token):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not token:
        raise ValueError("GitHub repository/token configuration missing")

    def api(path):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repository}/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError, ValueError):
            raise ValueError("GitHub release evidence unavailable; publishing denied") from None

    return api


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("tag")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--channel", choices=("beta", "stable"), default="beta")
    args = parser.parse_args()
    version = tag_version(args.tag)
    if args.publish:
        publish_intent(os.environ["GITHUB_EVENT_NAME"], os.environ["GITHUB_REF"], version, args.channel)

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], text=True).strip()

    sha = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or git("rev-parse", f"refs/tags/{args.tag}^{{commit}}") != sha:
        raise ValueError("tag/checkout SHA mismatch")
    # Trusted Publishing provenance uses the workflow event SHA, not an
    # arbitrary ref passed to checkout. A manual master run must therefore
    # refer to this exact release commit, not merely a later descendant.
    if args.publish and os.environ.get("GITHUB_SHA") != sha:
        raise ValueError("workflow event/checkout SHA mismatch; provenance would identify the wrong commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", sha, "origin/master"], check=True)
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("release checkout is not clean")
    config = configparser.ConfigParser()
    config.read(".bumpversion.cfg")
    if config["bumpversion"]["current_version"] != version or f"\n{version} (" not in Path("CHANGELOG.rst").read_text():
        raise ValueError("candidate/Changelog/tag mismatch")
    api = github_api(os.environ["GITHUB_REPOSITORY"], os.environ.get("GH_TOKEN"))
    check_remote(api, sha, publishing=args.publish)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"version={version}\nsha={sha}\n")
    print(f"release gates passed: {version} {sha}")


if __name__ == "__main__":
    main()
