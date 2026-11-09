"""Synthetic archive audits and corruption tests; no package download/build."""

import json
import runpy
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = runpy.run_path(str(ROOT / "ci/audit_packages.py"))
VERSION = "0.3.0a1"


def wheel_files():
    prefix = f"emtl-{VERSION}.dist-info/"
    metadata = (
        "Metadata-Version: 2.1\nName: emtl\n"
        f"Version: {VERSION}\nRequires-Python: <3.12,>=3.11\nLicense: MIT\nDescription-Content-Type: text/x-rst\n"
        "Classifier: Operating System :: POSIX :: Linux\n"
        "Classifier: Programming Language :: Python :: 3.11\n"
        + "".join(f"Requires-Dist: {item}\n" for item in sorted(AUDITOR["DEPENDENCIES"]))
        + "\nOverview\nChangelog\n"
    )
    return {
        **{f"emtl/{name}.py": b"# synthetic source\n" for name in AUDITOR["MODULES"]},
        prefix + "METADATA": metadata.encode(),
        prefix + "entry_points.txt": b"[console_scripts]\nemt = emtl.cli:run\n",
        prefix + "licenses/LICENSE": b"MIT\n",
        prefix + "licenses/AUTHORS.rst": b"Authors\n=======\n",
        prefix + "WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        prefix + "RECORD": b"",
    }


def write_wheel(tmp_path, files):
    path = tmp_path / f"emtl-{VERSION}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return path


def test_audit_records_exact_hash_metadata_and_file_list(tmp_path):
    files = wheel_files()
    report = AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)
    assert report["version"] == VERSION
    assert len(report["sha256"]) == 64
    assert report["files"] == sorted(files)
    assert f"emtl-{VERSION}.dist-info/licenses/AUTHORS.rst" in report["files"]
    assert set(report["requires_dist"]) == AUDITOR["DEPENDENCIES"]


@pytest.mark.parametrize("extra", ["tests/test_live.py", "../escape", "/absolute", "emtl/.env", "dist/coverage.xml"])
def test_audit_rejects_non_delivery_and_unsafe_files(tmp_path, extra):
    files = wheel_files()
    files[extra] = b"synthetic"
    with pytest.raises(ValueError, match="non-delivery|unsafe archive path"):
        AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)


@pytest.mark.parametrize(
    "extra",
    [f"emtl-{VERSION}.dist-info/licenses/OTHER.rst", f"emtl-{VERSION}.dist-info/AUTHORS.rst"],
)
def test_audit_rejects_unapproved_license_neighbors(tmp_path, extra):
    files = wheel_files()
    files[extra] = b"synthetic"
    with pytest.raises(ValueError, match="non-delivery file"):
        AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)


@pytest.mark.parametrize("bad_data", [b"-----BEGIN PRIVATE KEY-----", b"/Users/synthetic/workspace", b"/home/synthetic/workspace"])
def test_audit_rejects_sensitive_material_and_developer_paths(tmp_path, bad_data):
    files = wheel_files()
    files["emtl/core.py"] = bad_data
    with pytest.raises(ValueError, match="potential secret or developer path"):
        AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"0.3.0a1", b"0.2.6"),
        (b"rsa==4.9", b"rsa==4.8"),
        (b"cryptography==50.0.2", b"cryptography==42.0.5"),
        (b"<3.12,>=3.11", b">=3.10"),
        (b"emtl.cli:run", b"emtl.cli:other"),
    ],
)
def test_audit_rejects_version_dependency_python_or_entry_point_drift(tmp_path, old, new):
    files = {name: data.replace(old, new) for name, data in wheel_files().items()}
    with pytest.raises(ValueError, match="mismatch"):
        AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)


def test_audit_rejects_missing_module(tmp_path):
    files = wheel_files()
    del files["emtl/client.py"]
    with pytest.raises(ValueError, match="missing required"):
        AUDITOR["audit"](write_wheel(tmp_path, files), VERSION)


def test_sdist_audit_uses_real_archive_metadata_and_files(tmp_path):
    wheel = wheel_files()
    dist_root = f"emtl-{VERSION}.dist-info/"
    root = f"emtl-{VERSION}/"
    files = {root + "src/" + name: data for name, data in wheel.items() if name.startswith("emtl/")}
    files.update({root + name: b"synthetic\n" for name in AUDITOR["ROOT_FILES"]})
    assert root + "AUTHORS.rst" in files
    files[root + "PKG-INFO"] = wheel[dist_root + "METADATA"]
    files[root + "src/emtl.egg-info/entry_points.txt"] = wheel[dist_root + "entry_points.txt"]
    path = tmp_path / f"emtl-{VERSION}.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, BytesIO(data))
    assert AUDITOR["audit"](path, VERSION)["files"] == sorted(files)


@pytest.mark.parametrize("extra", ["tests/test_live.py", "ci/build.log", "AUTHORS-copy.rst"])
def test_sdist_rejects_unapproved_neighbors(tmp_path, extra):
    wheel = wheel_files()
    dist_root = f"emtl-{VERSION}.dist-info/"
    root = f"emtl-{VERSION}/"
    files = {root + "src/" + name: data for name, data in wheel.items() if name.startswith("emtl/")}
    files.update({root + name: b"synthetic\n" for name in AUDITOR["ROOT_FILES"]})
    files[root + "PKG-INFO"] = wheel[dist_root + "METADATA"]
    files[root + "src/emtl.egg-info/entry_points.txt"] = wheel[dist_root + "entry_points.txt"]
    files[root + extra] = b"synthetic"
    path = tmp_path / f"emtl-{VERSION}.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, BytesIO(data))
    with pytest.raises(ValueError, match="non-delivery file"):
        AUDITOR["audit"](path, VERSION)


def test_sdist_symlink_is_rejected_without_extraction(tmp_path):
    path = tmp_path / f"emtl-{VERSION}.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        item = tarfile.TarInfo("synthetic-link")
        item.type = tarfile.SYMTYPE
        item.linkname = "/synthetic"
        archive.addfile(item)
    with pytest.raises(ValueError, match="non-regular"):
        AUDITOR["audit"](path, VERSION)


def test_manifest_verification_never_rewrites_on_mismatch(tmp_path, monkeypatch):
    files = wheel_files()
    path = write_wheel(tmp_path, files)
    # Keep archive auditing real, replace only the list of artifacts to isolate
    # verification logic without constructing a second archive here.
    sdist = tmp_path / f"emtl-{VERSION}.tar.gz"
    sdist.write_bytes(b"synthetic sdist")
    reports = [AUDITOR["audit"](path, VERSION), {"filename": sdist.name, "sha256": "synthetic"}]
    manifest = tmp_path / "manifest.json"
    original = json.dumps(reports)
    manifest.write_text(original)
    sums = tmp_path / "SHA256SUMS"
    sums.write_text("".join(f"{item['sha256']}  {item['filename']}\n" for item in reports))
    main = AUDITOR["main"]
    monkeypatch.setitem(main.__globals__, "audit", lambda path, version: next(item for item in reports if item["filename"] == path.name))
    monkeypatch.setattr(sys, "argv", ["audit", str(tmp_path), VERSION, "--verify"])
    main()
    assert manifest.read_text() == original
    manifest.write_text("[]")
    with pytest.raises(SystemExit, match="manifest mismatch"):
        main()
    assert manifest.read_text() == "[]"
    manifest.write_text(original)
    sums.write_text("tampered\n")
    with pytest.raises(SystemExit, match="manifest mismatch"):
        main()
    assert sums.read_text() == "tampered\n"
