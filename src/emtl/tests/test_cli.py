import subprocess


def test_main():
    assert subprocess.check_output(["emt", "-u=foo", "-p=bar"], text=True) == "('foo', 'bar')\n"
