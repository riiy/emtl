import os

from .. import emt
from .. import login


def test_emt():
    assert emt("user", "pass") == ("user", "pass")


def test_emt_empty():
    assert emt("", "") == ("", "")


def test_login():
    assert len(login(os.getenv("EM_USERNAME", ""), os.getenv("EM_PASSWORD", ""))) == len("b91d8012-b70b-4265-bb5d-f79442531017")
