"""P3 R3: isolated, post-collection HTTP logging fault mutations."""

import ast
import inspect
import json
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pytest.ini").is_file())
sys.path.insert(0, str(ROOT))
TARGETS = {
    "late_error": ("tests/test_client_logging.py", "safe_http_error_is_established_before_logging"),
    "reraise_handler": ("tests/test_client_logging.py", "non_trade_http_error_survives_handler_failure"),
    "handler_cause": ("tests/test_client_logging.py", "non_trade_http_error_survives_handler_failure"),
    "handler_message": ("tests/test_client_logging.py", "non_trade_http_error_survives_handler_failure"),
    "swallow_base": ("tests/test_client_logging.py", "non_trade_http_handler_base_exception_propagates"),
    "late_status": ("tests/test_trade_errors.py", "trade_http_status_requires_response_source"),
}


class Mutation:
    def __init__(self, kind):
        self.kind = kind

    def pytest_collection_modifyitems(self, session, config, items):
        from emtl import client as module

        import conftest

        assert conftest._offline["install"].__globals__["_installed"]
        tree = ast.parse(textwrap.dedent(inspect.getsource(module.TradingClient._check_resp)))
        function = tree.body[0]
        branch = function.body[-1]
        assert isinstance(branch, ast.If)
        error, observer, guarded_log, final_raise = branch.body
        assert isinstance(error, ast.Assign)
        assert error.targets[0].id == "error"
        assert isinstance(observer, ast.If)
        assert isinstance(guarded_log, ast.Try)
        assert len(guarded_log.handlers) == 1
        handler = guarded_log.handlers[0]
        assert isinstance(handler.type, ast.Name)
        assert handler.type.id == "Exception"
        assert isinstance(final_raise, ast.Raise)
        if self.kind == "late_error":
            branch.body = [observer, guarded_log, error, final_raise]
        elif self.kind == "reraise_handler":
            handler.body = [ast.Raise()]
        elif self.kind == "handler_cause":
            handler.name = "handler_error"
            handler.body = [ast.Raise(exc=ast.Name(id="error", ctx=ast.Load()), cause=ast.Name(id="handler_error", ctx=ast.Load()))]
        elif self.kind == "handler_message":
            handler.name = "handler_error"
            handler.body = ast.parse('error.args = (str(error) + ": " + str(handler_error),)').body
        elif self.kind == "swallow_base":
            handler.type = ast.Name(id="BaseException", ctx=ast.Load())
        else:
            assert self.kind == "late_status"
            branch.body = [error, guarded_log, final_raise]
            guarded_log.body.append(observer)
        compiled = {}
        # Real module globals preserve the construction observer seam in the order test.
        exec(compile(ast.fix_missing_locations(tree), "<p3-r3-http-log-mutation>", "exec"), vars(module), compiled)  # noqa: S102
        module.TradingClient._check_resp = compiled[function.name]


if __name__ == "__main__":
    kind = sys.argv[1]
    path, selection = TARGETS[kind]
    output = ROOT / "dist/p3-r3"
    output.mkdir(parents=True, exist_ok=True)
    args = [path, "-k", selection, "-p", "no:cacheprovider", "-vv", f"--junitxml={output / ('mutation-' + kind + '.xml')}"]
    code = int(pytest.main(args, plugins=[Mutation(kind)]))
    (output / f"mutation-{kind}.json").write_text(json.dumps({"kind": kind, "pytest_args": args, "exit_code": code}, indent=2))
    raise SystemExit(code)
