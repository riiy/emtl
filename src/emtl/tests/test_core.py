from .. import emt


def test_emt():
    assert emt([b"a", b"bc", b"abc"]) == b"abc"
