"""P3 evidence only: one in-memory mutation after guarded pytest collection."""

import inspect
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pytest.ini").is_file())
sys.path.insert(0, str(ROOT))


class Mutation:
    def pytest_collection_modifyitems(self, session, config, items):
        from emtl import _protocol
        from emtl import client as module
        from emtl.errors import TradeOutcomeUnknown

        import conftest

        assert conftest._offline["install"].__globals__["_installed"]
        original = module.TradingClient._execute_trade
        if kind == "early":

            def execute(self, operation, data):
                try:
                    return original(self, operation, data)
                except Exception:
                    raise TradeOutcomeUnknown(operation, "exchange_error") from None

            module.TradingClient._execute_trade = execute
        elif kind in {"remove", "post_only"}:

            def execute(self, operation, data):
                if kind == "remove":
                    reply = self._query_something(operation, req_data=data)
                else:
                    try:
                        reply = self._query_something(operation, req_data=data)
                    except Exception:
                        raise TradeOutcomeUnknown(operation, "exchange_error") from None
                return _protocol.order_result(reply, module.logger) if operation == "create_order" else _protocol.cancel_result(reply)

            module.TradingClient._execute_trade = execute
        elif kind in {"replay", "query", "login"}:

            def execute(self, operation, data):
                try:
                    return original(self, operation, data)
                except TradeOutcomeUnknown:
                    try:
                        if kind == "replay":
                            original(self, operation, data)
                        elif kind == "query":
                            self.query_orders()
                        else:
                            self.login()
                    except Exception:  # noqa: S110 - deliberately bad compensation; never log its exception.
                        pass
                    raise

            module.TradingClient._execute_trade = execute
        elif kind == "redirect":
            query = _protocol.query

            def follow(*args, **kwargs):
                kwargs["disable_order_redirects"] = False
                return query(*args, **kwargs)

            _protocol.query = follow
        elif kind in {"implicit_context", "explicit_cause"}:
            source = textwrap.dedent(inspect.getsource(original))
            if kind == "implicit_context":
                source = source.replace(" from None", "")
            else:
                source = source.replace("except Exception:", "except Exception as error:")
                source = source.replace(" from None", " from error")
            namespace = dict(vars(module))
            exec(compile(source, "<p3-memory-mutation>", "exec"), namespace)  # noqa: S102 - own source, isolated test process only.
            module.TradingClient._execute_trade = namespace["_execute_trade"]
        elif kind == "business":
            result = _protocol.order_result

            def clone(*args, **kwargs):
                value = result(*args, **kwargs)
                return dict(value) if isinstance(value, dict) else value

            _protocol.order_result = clone
        else:
            raise AssertionError("unknown mutation")


targets = {
    "early": ["tests/test_trade_errors.py", "-k", "test_k1"],
    "remove": ["tests/test_trade_errors.py", "-k", "test_k2"],
    "post_only": ["tests/test_trade_errors.py", "-k", "test_k3"],
    "replay": ["tests/test_trade_errors.py", "-k", "test_k2"],
    "query": ["tests/test_trade_errors.py", "-k", "test_k2"],
    "login": ["tests/test_trade_errors.py", "-k", "test_k2"],
    "redirect": ["tests/test_client_operations.py", "-k", "test_redirect_cannot"],
    "implicit_context": ["tests/test_client_logging.py", "-k", "test_new_errors_and_standard_traceback"],
    "explicit_cause": ["tests/test_client_logging.py", "-k", "test_new_errors_and_standard_traceback"],
    "business": ["tests/test_trade_errors.py", "-k", "test_k4_second"],
}
if __name__ == "__main__":
    kind = sys.argv[1]
    args = [*targets[kind], "-p", "no:cacheprovider", "-vv", f"--junitxml=dist/p3-local/mutation-{kind}.xml"]
    code = int(pytest.main(args, plugins=[Mutation()]))
    (ROOT / f"dist/p3-local/mutation-{kind}.json").write_text(
        json.dumps({"mutation": kind, "pytest_args": args, "exit_code": code}, indent=2)
    )
    raise SystemExit(code)
