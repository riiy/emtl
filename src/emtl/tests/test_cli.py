import subprocess


def test_main():
    assert subprocess.check_output(["emt", "foo", "foobar"], text=True) == "foobar\n"
