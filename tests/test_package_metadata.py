"""Approved release metadata contracts; no build frontend or network required."""

import configparser
import runpy
from importlib import metadata
from pathlib import Path

import pytest
import setuptools

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def package_metadata(monkeypatch):
    captured = {}
    monkeypatch.setattr(setuptools, "setup", lambda **kwargs: captured.update(kwargs))
    runpy.run_path(str(ROOT / "setup.py"))
    return captured


def test_python_and_platform_claims_match_approved_scope(package_metadata):
    assert package_metadata["python_requires"] == ">=3.11,<3.12"
    classifiers = package_metadata["classifiers"]
    assert [item for item in classifiers if item.startswith("Operating System ::")] == ["Operating System :: POSIX :: Linux"]
    assert [item for item in classifiers if item.startswith("Programming Language :: Python :: 3.")] == [
        "Programming Language :: Python :: 3.11"
    ]


def test_runtime_dependencies_are_not_silently_upgraded(package_metadata):
    assert package_metadata["install_requires"] == ["rsa==4.9", "requests==2.31.0", "ddddocr==1.4.11", "cryptography==42.0.5"]
    assert package_metadata["entry_points"] == {"console_scripts": ["emt = emtl.cli:run"]}
    assert package_metadata["long_description_content_type"] == "text/x-rst"


def test_candidate_fallbacks_and_manual_git_boundary(package_metadata, monkeypatch, capsys):
    candidate = "0.3.0a1"
    assert package_metadata["use_scm_version"]["fallback_version"] == candidate
    config = configparser.ConfigParser()
    config.read(ROOT / ".bumpversion.cfg")
    assert config["bumpversion"]["current_version"] == candidate
    assert not config["bumpversion"].getboolean("commit")
    assert not config["bumpversion"].getboolean("tag")
    assert f'__version__ = "{candidate}"' in (ROOT / "src/emtl/__init__.py").read_text()
    assert f'version: "{candidate}"' in (ROOT / ".cookiecutterrc").read_text()

    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing)
    conf = runpy.run_path(str(ROOT / "docs/conf.py"))
    assert conf["version"] == conf["release"] == candidate
    assert capsys.readouterr().err == ""


def test_docs_use_supported_python_and_separate_online_linkcheck():
    assert 'python: "3.11"' in (ROOT / ".readthedocs.yml").read_text()
    assert "formats: []" in (ROOT / ".readthedocs.yml").read_text()
    config = configparser.ConfigParser()
    config.read(ROOT / "tox.ini")
    assert "-b html" in config["testenv:docs"]["commands"]
    assert "linkcheck" not in config["testenv:docs"]["commands"]
    assert "-b linkcheck" in config["testenv:linkcheck"]["commands"]


def test_maintenance_configuration_has_review_trigger_and_private_contact():
    updates = (ROOT / ".github/dependabot.yml").read_text()
    assert updates.count("interval: monthly") == 4
    for directory in ("/", "/ci", "/docs"):
        assert f"directory: {directory}\n" in updates
    assert "package-ecosystem: github-actions" in updates
    security = (ROOT / "SECURITY.md").read_text()
    assert "riiyzhou@gmail.com" in security
    assert "Private Vulnerability Reporting was disabled" in security
    assert "Never send credentials" in security
