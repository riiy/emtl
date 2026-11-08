"""P3 R2 test evidence: scoped source mutations after offline collection."""

import inspect
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pytest.ini").is_file())
sys.path.insert(0, str(ROOT))


class Mutation:
    def __init__(self, kind):
        self.kind = kind

    def pytest_collection_modifyitems(self, session, config, items):
        from emtl import client as module

        import conftest

        assert conftest._offline["install"].__globals__["_installed"]
        name = "_execute_trade" if self.kind == "exception_source" else "_check_resp"
        source = textwrap.dedent(inspect.getsource(getattr(module.TradingClient, name)))
        if self.kind == "exception_source":
            old = 'if http_status is not None:\n            raise TradeOutcomeUnknown(operation, "http_status", http_status) from None'
            new = 'if isinstance(error, BrokerHTTPError):\n            raise TradeOutcomeUnknown(operation, "http_status", error.status_code) from None'
            assert source.count(old) == 1
            source = source.replace("except Exception:", "except Exception as error:", 1).replace(old, new)
        else:
            old = '        if on_http_status is not None:\n            on_http_status(status)\n        logger.error("request failed, code=%s", status)'
            new = '        logger.error("request failed, code=%s", status)\n        if on_http_status is not None:\n            on_http_status(status)'
            assert self.kind == "late_source"
            assert source.count(old) == 1
            source = source.replace(old, new)
        namespace = dict(vars(module))
        exec(compile(source, "<p3-r2-source-mutation>", "exec"), namespace)  # noqa: S102 - own source, isolated offline process.
        setattr(module.TradingClient, name, namespace[name])


if __name__ == "__main__":
    kind = sys.argv[1]
    assert kind in {"exception_source", "late_source"}
    output = ROOT / "dist/p3-r2"
    output.mkdir(parents=True, exist_ok=True)
    args = [
        "tests/test_trade_errors.py",
        "-k",
        "trade_http_status_requires_response_source",
        "-p",
        "no:cacheprovider",
        "-vv",
        f"--junitxml={output / ('mutation-' + kind + '.xml')}",
    ]
    code = int(pytest.main(args, plugins=[Mutation(kind)]))
    (output / f"mutation-{kind}.json").write_text(json.dumps({"kind": kind, "pytest_args": args, "exit_code": code}, indent=2))
    raise SystemExit(code)
