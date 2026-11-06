"""Install test isolation before pytest collects the emtl package."""

import os
import runpy
from pathlib import Path

_credentials = {name: os.environ.pop(name, None) for name in ("EM_USERNAME", "EM_PASSWORD")}
_offline = runpy.run_path(str(Path(__file__).parent / "tests/_offline.py"))
_offline["install"]()


def pytest_unconfigure(config):
    _offline["restore"]()
    for name, value in _credentials.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
