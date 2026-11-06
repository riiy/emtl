"""Linux network-namespace check, independent of pytest and its guard."""

import errno
import socket
from pathlib import Path

interfaces = {path.name for path in Path("/sys/class/net").iterdir()}
assert interfaces == {"lo"}, "unexpected network interface"
routes = Path("/proc/net/route").read_text().splitlines()[1:]
assert not any(line.split()[1] == "00000000" for line in routes), "default route exists"
with socket.socket() as sock:
    sock.settimeout(2)
    try:
        sock.connect(("192.0.2.1", 9))
    except OSError as exc:
        if exc.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH):
            raise
    else:
        raise AssertionError("unexpected network access")
print("OS network namespace isolation verified")
