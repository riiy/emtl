"""Fail-closed sdist/wheel content and metadata audit; never imports emtl."""

import argparse
import configparser
import hashlib
import json
import re
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path
from pathlib import PurePosixPath

from packaging.version import Version

MODULES = {"__init__", "__main__", "_coordination", "_protocol", "_version", "cli", "client", "const", "core", "errors", "utils"}
DEPENDENCIES = {"rsa==4.9", "requests==2.33.1", "ddddocr==1.4.11", "cryptography==50.0.2"}
EGG_FILES = {"PKG-INFO", "SOURCES.txt", "dependency_links.txt", "entry_points.txt", "requires.txt", "top_level.txt", "not-zip-safe"}
ROOT_FILES = {"MANIFEST.in", "LICENSE", "AUTHORS.rst", "README.rst", "CHANGELOG.rst", "setup.py", "setup.cfg", "pyproject.toml", "PKG-INFO"}
DIST_FILES = {"METADATA", "WHEEL", "RECORD", "entry_points.txt", "top_level.txt", "LICENSE", "licenses/LICENSE", "licenses/AUTHORS.rst"}


def read_archive(path):
    files = {}
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                if not item.is_dir():
                    if item.filename in files or item.external_attr >> 16 & 0o170000 == 0o120000:
                        raise ValueError("duplicate or symlink in wheel")
                    files[item.filename] = archive.read(item)
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            for item in archive.getmembers():
                if item.isdir():
                    continue
                if not item.isfile() or item.name in files:
                    raise ValueError("non-regular or duplicate sdist member")
                files[item.name] = archive.extractfile(item).read()
    else:
        raise ValueError("unexpected artifact type")
    if not files:
        raise ValueError("empty artifact")
    for name, data in files.items():
        parts = PurePosixPath(name).parts
        if PurePosixPath(name).is_absolute() or ".." in parts or "\\" in name:
            raise ValueError("unsafe archive path")
        if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|/Users/|/home/", data):
            raise ValueError("potential secret or developer path in artifact")
    return files


def audit(path, expected_version):
    if str(Version(expected_version)) != expected_version:
        raise ValueError("expected version is not canonical")
    files = read_archive(path)
    wheel = path.name.endswith(".whl")
    if path.name != (f"emtl-{expected_version}-py3-none-any.whl" if wheel else f"emtl-{expected_version}.tar.gz"):
        raise ValueError("artifact filename mismatch")
    root = f"emtl-{expected_version}/"
    dist_root = f"emtl-{expected_version}.dist-info/"
    required = {f"{'emtl/' if wheel else root + 'src/emtl/'}{module}.py" for module in MODULES}
    metadata_path = f"{dist_root}METADATA" if wheel else root + "PKG-INFO"
    entry_path = f"{dist_root}entry_points.txt" if wheel else root + "src/emtl.egg-info/entry_points.txt"
    required.update({metadata_path, entry_path, dist_root + "licenses/LICENSE" if wheel else root + "LICENSE"})
    if wheel:
        required.update({dist_root + "WHEEL", dist_root + "RECORD"})
    else:
        required.update(root + name for name in ("README.rst", "CHANGELOG.rst", "setup.py", "pyproject.toml", "MANIFEST.in"))
    if not required <= files.keys():
        raise ValueError("missing required package files")
    for name in files:
        if name in required:
            continue
        if wheel:
            allowed = name.startswith(dist_root) and name[len(dist_root) :] in DIST_FILES
        else:
            relative = name.removeprefix(root)
            allowed = name.startswith(root) and (
                relative in ROOT_FILES or (relative.startswith("src/emtl.egg-info/") and relative.rsplit("/", 1)[-1] in EGG_FILES)
            )
        if not allowed:
            raise ValueError("non-delivery file in artifact")
    metadata = BytesParser().parsebytes(files[metadata_path])
    if metadata["Name"] != "emtl" or metadata["Version"] != expected_version:
        raise ValueError("artifact version/name mismatch")
    if metadata["Requires-Python"] != ">=3.11,<3.12" and metadata["Requires-Python"] != "<3.12,>=3.11":
        raise ValueError("Python support metadata mismatch")
    dependencies = set(metadata.get_all("Requires-Dist", []))
    if dependencies != DEPENDENCIES:
        raise ValueError("dependency metadata mismatch")
    if metadata["License"] != "MIT" or metadata["Description-Content-Type"] != "text/x-rst" or "Changelog" not in metadata.get_payload():
        raise ValueError("license or README/Changelog metadata missing")
    classifiers = metadata.get_all("Classifier", [])
    if [item for item in classifiers if item.startswith("Operating System ::")] != ["Operating System :: POSIX :: Linux"]:
        raise ValueError("OS metadata mismatch")
    if [item for item in classifiers if item.startswith("Programming Language :: Python :: 3.")] != [
        "Programming Language :: Python :: 3.11"
    ]:
        raise ValueError("Python classifier mismatch")
    entries = configparser.ConfigParser()
    entries.read_string(files[entry_path].decode())
    if dict(entries["console_scripts"]) != {"emt": "emtl.cli:run"}:
        raise ValueError("CLI entry point mismatch")
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "version": expected_version,
        "requires_python": metadata["Requires-Python"],
        "requires_dist": sorted(dependencies),
        "files": sorted(files),
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("expected_version")
    parser.add_argument("--verify", action="store_true", help="compare against an existing manifest, without rewriting it")
    args = parser.parse_args()
    paths = sorted([*args.directory.glob("*.whl"), *args.directory.glob("*.tar.gz")])
    if len(paths) != 2 or sum(path.name.endswith(".whl") for path in paths) != 1:
        raise SystemExit("exactly one wheel and one sdist required")
    report = [audit(path, args.expected_version) for path in paths]
    manifest = args.directory / "manifest.json"
    sums = args.directory / "SHA256SUMS"
    expected_sums = "".join(f"{item['sha256']}  {item['filename']}\n" for item in report)
    if args.verify:
        if json.loads(manifest.read_text()) != report or sums.read_text() != expected_sums:
            raise SystemExit("artifact manifest mismatch")
    else:
        manifest.write_text(json.dumps(report, indent=2) + "\n")
        sums.write_text(expected_sums)
    print("package contents, metadata and SHA256 verified")


if __name__ == "__main__":
    main()
