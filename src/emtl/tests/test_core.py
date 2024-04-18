import os
from typing import Optional

from .. import emt
from .. import login
from .. import query_asset_and_position
from ..utils import Response


def test_emt():
    assert emt("user", "pass") == ("user", "pass")


def test_emt_empty():
    assert emt("", "") == ("", "")


def test_login():
    validate_key = login(os.getenv("EM_USERNAME", ""), os.getenv("EM_PASSWORD", ""))
    if validate_key:
        assert len(validate_key) == len("b91d8012-b70b-4265-bb5d-f79442531017")


def test_query_asset_position():
    resp: Optional[Response] = query_asset_and_position()
    if resp:
        assert resp.error_code == 0
