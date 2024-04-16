from .. import emt
from .. import login


def test_emt():
    assert emt("user", "pass") == ("user", "pass")


def test_emt_empty():
    assert emt("", "") == ("", "")


def test_login():
    assert login("user", "pass") == "userpass"
