"""Installed-artifact smoke, run outside the checkout under OS network denial."""

import argparse
import inspect
import json
import os
import subprocess
import sys
import sysconfig
from importlib.metadata import distribution
from importlib.metadata import distributions
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("expected_version")
    args = parser.parse_args()
    for name in list(os.environ):
        if name.startswith("EM_") or name in ("NETRC", "SSH_AUTH_SOCK", "SSH_AGENT_PID", "PYTHONPATH"):
            os.environ.pop(name, None)

    # Observe attempts too: OS denial alone could hide a swallowed request.
    attempts = []

    def deny_network(event, values):
        if event in ("socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.gethostbyname"):
            attempts.append(event)
            raise RuntimeError("network attempt during package smoke")

    sys.addaudithook(deny_network)
    import emtl
    from emtl import TradingClient
    from emtl import core
    from emtl.errors import BrokerHTTPError
    from emtl.errors import TradeOutcomeUnknown

    installed = distribution("emtl")
    assert emtl.__version__ == installed.version == args.expected_version
    assert Path(emtl.__file__).is_relative_to(Path(sysconfig.get_path("purelib")))
    signatures = {
        "login": "(username: str = '', password: str = '', duration: int = 30) -> Optional[str]",
        "query_asset_and_position": "()",
        "query_orders": "()",
        "query_history_orders": "(size, start_time, end_time)",
        "query_trades": "()",
        "query_history_trades": "(size, start_time, end_time)",
        "query_funds_flow": "(size, start_time, end_time)",
        "create_order": "(stock_code, trade_type, market: str, price: float, amount: int)",
        "cancel_order": "(order_str: str)",
    }
    assert emtl.__all__ == [*signatures, "TradingClient"]
    for name, signature in signatures.items():
        assert getattr(emtl, name) is getattr(core, name)
        assert str(inspect.signature(getattr(emtl, name))) == signature
    assert issubclass(TradeOutcomeUnknown, RuntimeError)
    assert issubclass(BrokerHTTPError, RuntimeError)
    entries = {entry.name: entry.value for entry in installed.entry_points if entry.group == "console_scripts"}
    assert entries == {"emt": "emtl.cli:run"}
    client = TradingClient("P4_FAKE_ACCOUNT", "P4_FAKE_PASSWORD")
    client.close()
    assert not attempts, "import or constructor attempted network access"
    for command in ([str(Path(sys.executable).parent / "emt"), "--help"], [sys.executable, "-m", "emtl", "--help"]):
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=True)
        assert "usage:" in result.stdout.lower()
        assert "P4_FAKE_" not in result.stdout + result.stderr
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True, timeout=30)
    print(
        json.dumps(
            {
                "version": installed.version,
                "module": emtl.__file__,
                "api_cli_constructor": "PASS",
                "dependencies": {item.metadata["Name"]: item.version for item in distributions()},
            }
        )
    )


if __name__ == "__main__":
    main()
