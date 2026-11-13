"""All GitHub evidence is synthetic; never contacts GitHub or a package index."""

import copy
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = runpy.run_path(str(ROOT / "ci/release_gate.py"))
SHA = "a" * 40


@pytest.mark.parametrize("tag", ["v0.3.0a1", "v0.3.0b1", "v0.3.0b2", "v0.3.0rc1", "v0.3.0"])
def test_release_tag_accepts_canonical_pep440(tag):
    assert GATE["tag_version"](tag) == tag[1:]


@pytest.mark.parametrize("tag", ["random", "0.3.0", "v00.3.0", "v0.3", "v0.3.0+local", "v0.3.0.dev1", "v0.3.0\n", "v0.3.0;echo"])
def test_release_tag_rejects_noncanonical_or_unsafe_values(tag):
    with pytest.raises(ValueError, match="release tag"):
        GATE["tag_version"](tag)


@pytest.mark.parametrize(
    ("event", "ref", "version", "channel"),
    [
        ("pull_request", "refs/pull/1/merge", "0.3.0", "stable"),
        ("push", "refs/tags/v0.3.0", "0.3.0", "stable"),
        ("workflow_dispatch", "refs/heads/unmerged", "0.3.0", "stable"),
        ("workflow_dispatch", "refs/heads/master", "0.3.0a1", "beta"),
        ("workflow_dispatch", "refs/heads/master", "0.3.0b1", "stable"),
        ("workflow_dispatch", "refs/heads/master", "0.3.0", "beta"),
    ],
)
def test_publish_intent_fails_closed(event, ref, version, channel):
    with pytest.raises(ValueError, match="publishing"):
        GATE["publish_intent"](event, ref, version, channel)


@pytest.mark.parametrize(("version", "channel"), [("0.3.0b1", "beta"), ("0.3.0b2", "beta"), ("0.3.0rc1", "beta"), ("0.3.0", "stable")])
def test_manual_publish_intent_still_needs_other_gates(version, channel):
    GATE["publish_intent"]("workflow_dispatch", "refs/heads/master", version, channel)


def remote_evidence():
    data = {}
    for index, (workflow, jobs) in enumerate(GATE["REQUIRED_WORKFLOWS"].items()):
        data[workflow] = {
            "workflow_runs": [
                {"id": index, "head_sha": SHA, "head_branch": "master", "event": "push", "status": "completed", "conclusion": "success"}
            ]
        }
        data[str(index)] = {
            "total_count": len(jobs),
            "jobs": [{"name": name, "status": "completed", "conclusion": "success"} for name in sorted(jobs)],
        }
    data["pypi"] = {"protection_rules": [{"type": "required_reviewers", "reviewers": [{"type": "User", "reviewer": {"id": 1}}]}]}
    return data


def api_for(data):
    def api(path):
        parts = path.split("/")
        if parts[0] == "environments":
            return data["pypi"]
        if parts[1] == "workflows":
            return data[parts[2]]
        return data[parts[2]]

    return api


def test_exact_sha_and_real_required_reviewer_evidence():
    GATE["check_remote"](api_for(remote_evidence()), SHA, publishing=True)


@pytest.mark.parametrize("field", ["head_sha", "head_branch", "event", "status", "conclusion"])
def test_release_rejects_wrong_sha_pr_or_failed_ci(field):
    data = remote_evidence()
    data["github-actions.yml"]["workflow_runs"][0][field] = "wrong"
    with pytest.raises(ValueError, match="exact-SHA"):
        GATE["check_remote"](api_for(data), SHA, publishing=True)


def test_newer_failed_run_cannot_be_hidden_by_an_old_success():
    data = remote_evidence()
    failed = dict(data["github-actions.yml"]["workflow_runs"][0], conclusion="failure")
    data["github-actions.yml"]["workflow_runs"].insert(0, failed)
    with pytest.raises(ValueError, match="exact-SHA"):
        GATE["check_remote"](api_for(data), SHA, publishing=True)


@pytest.mark.parametrize("failure", ["skipped", "missing", "incomplete"])
def test_release_rejects_incomplete_job_evidence(failure):
    data = remote_evidence()
    if failure == "skipped":
        data["0"]["jobs"][0]["conclusion"] = "skipped"
    elif failure == "missing":
        data["0"]["jobs"][0]["name"] = "not required"
    else:
        data["0"]["total_count"] += 1
    with pytest.raises(ValueError, match="job evidence|CI job"):
        GATE["check_remote"](api_for(data), SHA, publishing=True)


@pytest.mark.parametrize("rules", [[], [{"type": "required_reviewers", "reviewers": []}], [{"type": "wait_timer"}]])
def test_environment_name_without_reviewers_does_not_authorize_upload(rules):
    data = copy.deepcopy(remote_evidence())
    data["pypi"]["protection_rules"] = rules
    with pytest.raises(ValueError, match="required reviewers"):
        GATE["check_remote"](api_for(data), SHA, publishing=True)
    GATE["check_remote"](api_for(data), SHA, publishing=False)


@pytest.mark.parametrize("condition", ["clean", "wrong_tag_sha", "unmerged", "dirty", "wrong_candidate", "wrong_changelog"])
def test_main_checks_checkout_tag_ancestry_cleanliness_and_candidate(monkeypatch, tmp_path, condition):
    main = runpy.run_path(str(ROOT / "ci/release_gate.py"))["main"]
    monkeypatch.chdir(tmp_path)
    candidate = "0.3.0b1" if condition == "wrong_candidate" else "0.3.0a1"
    (tmp_path / ".bumpversion.cfg").write_text(f"[bumpversion]\ncurrent_version = {candidate}\n")
    (tmp_path / "CHANGELOG.rst").write_text("\nwrong (" if condition == "wrong_changelog" else "\n0.3.0a1 (unreleased)\n")
    monkeypatch.setattr(sys, "argv", ["release_gate", "v0.3.0a1"])
    monkeypatch.setenv("GITHUB_REPOSITORY", "synthetic/emtl")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    monkeypatch.setitem(main.__globals__, "github_api", lambda *args: api_for(remote_evidence()))

    def git(args, **kwargs):
        if args[1] == "status":
            return "M synthetic.py\n" if condition == "dirty" else ""
        if "refs/tags" in args[-1] and condition == "wrong_tag_sha":
            return "b" * 40
        return SHA

    def ancestor(args, **kwargs):
        assert args == ["git", "merge-base", "--is-ancestor", SHA, "origin/master"]
        if condition == "unmerged":
            raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(subprocess, "check_output", git)
    monkeypatch.setattr(subprocess, "run", ancestor)
    if condition == "unmerged":
        with pytest.raises(subprocess.CalledProcessError):
            main()
    elif condition != "clean":
        with pytest.raises(ValueError, match="mismatch|not clean"):
            main()
    else:
        main()
        assert (tmp_path / "output").read_text() == f"version=0.3.0a1\nsha={SHA}\n"


def test_release_workflow_limits_oidc_and_reuses_the_tested_artifact():
    text = (ROOT / ".github/workflows/release.yml").read_text()
    build, publish = text.split("\n  publish:\n", 1)
    assert "id-token: write" not in build
    assert publish.count("id-token: write") == 1
    assert "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/master' && inputs.publish" in publish
    assert "name: pypi" in publish
    assert "--publish" in publish
    assert "--verify" in publish
    assert text.count("python -m build") == 1
    assert text.count("name: release-distributions") == 3
    assert "sha256sum --check ../release/SHA256SUMS" in publish
    assert "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086" in publish
    assert "skip-existing" not in text


@pytest.mark.parametrize("matches", [True, False])
def test_manual_upload_provenance_must_identify_the_tested_commit(monkeypatch, tmp_path, matches):
    main = runpy.run_path(str(ROOT / "ci/release_gate.py"))["main"]
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".bumpversion.cfg").write_text("[bumpversion]\ncurrent_version = 0.3.0b1\n")
    (tmp_path / "CHANGELOG.rst").write_text("\n0.3.0b1 (candidate)\n")
    monkeypatch.setattr(sys, "argv", ["release_gate", "v0.3.0b1", "--publish"])
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/master")
    monkeypatch.setenv("GITHUB_SHA", SHA if matches else "b" * 40)
    monkeypatch.setenv("GITHUB_REPOSITORY", "synthetic/emtl")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setattr(subprocess, "check_output", lambda args, **kwargs: "" if args[1] == "status" else SHA)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setitem(main.__globals__, "github_api", lambda *args: api_for(remote_evidence()))
    if matches:
        main()
    else:
        with pytest.raises(ValueError, match="event/checkout SHA mismatch"):
            main()


def test_alpha_and_documentation_workflows_have_no_publish_privilege():
    alpha = (ROOT / ".github/workflows/packages.yml").read_text()
    docs = (ROOT / ".github/workflows/document.yml").read_text()
    assert "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_EMTL" in alpha
    assert "ci/run_package_smoke.py" in alpha
    for text in (alpha, docs):
        assert "id-token:" not in text
        assert "gh-action-pypi-publish" not in text
    assert "push:" not in docs
    assert "assert not Version(version).is_prerelease" in docs
    assert "https://pypi.org/pypi/emtl/" in docs


@pytest.mark.parametrize("workflow", ["release.yml", "document.yml"])
def test_candidate_cannot_replace_the_trusted_validator(workflow):
    text = (ROOT / ".github/workflows" / workflow).read_text()
    candidate_checkout = "ref: ${{ env.RELEASE_TAG }}"
    stage = "cp ci/release_gate.py"
    trusted_run = 'python -I "$RUNNER_TEMP/emtl-release-tools/release_gate.py"'
    assert text.index(stage) < text.index(candidate_checkout) < text.index(trusted_run)
    assert text.index(trusted_run) < text.index("python -m pip install -r ci/requirements.txt")
    assert "python ci/release_gate.py" not in text
    if workflow == "release.yml":
        publish = text.split("\n  publish:\n", 1)[1]
        assert publish.index("ref: ${{ github.sha }}") < publish.index(stage) < publish.index(candidate_checkout)
        assert 'python -I "$RUNNER_TEMP/emtl-release-tools/audit_packages.py"' in publish
        assert "python ci/audit_packages.py" not in publish


@pytest.mark.parametrize("failure", ["missing", "failed", "skipped", "wrong_sha"])
def test_release_requires_successful_package_alpha_for_exact_sha(failure):
    data = remote_evidence()
    if failure == "missing":
        data["packages.yml"]["workflow_runs"] = []
    elif failure == "failed":
        data["packages.yml"]["workflow_runs"][0]["conclusion"] = "failure"
    elif failure == "skipped":
        data["2"]["jobs"][0]["conclusion"] = "skipped"
    else:
        data["packages.yml"]["workflow_runs"][0]["head_sha"] = "b" * 40

    with pytest.raises(ValueError, match="exact-SHA|CI job"):
        GATE["check_remote"](api_for(data), SHA, publishing=True)


def test_release_gate_requires_package_alpha_workflow():
    assert GATE["REQUIRED_WORKFLOWS"]["packages.yml"] == {"package"}


def test_pypi_approval_probe_has_no_publish_or_oidc_permission():
    probe = (ROOT / ".github/workflows/pypi-approval-probe.yml").read_text()
    assert "workflow_dispatch:" in probe
    assert "environment:" in probe
    assert "name: pypi" in probe
    assert "permissions: {}" in probe
    assert "id-token:" not in probe
    assert "gh-action-pypi-publish" not in probe
    assert "pip install" not in probe
    assert "python -m build" not in probe
