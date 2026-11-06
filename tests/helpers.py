"""Small factories for synthetic protocol responses."""

import json
from pathlib import Path

from requests import Response

OFFLINE_HELPER = Path(__file__).with_name("_offline.py")
QUERY_CALLS = [
    ("query_asset_and_position", ()),
    ("query_orders", ()),
    ("query_trades", ()),
    ("query_history_orders", (10, "start", "end")),
    ("query_history_trades", (10, "start", "end")),
    ("query_funds_flow", (10, "start", "end")),
]


def response(value=None, text=None, status=200):
    result = Response()
    result.status_code = status
    result._content = (json.dumps(value) if text is None else text).encode()
    return result


def protocol_cases():
    return json.loads((Path(__file__).parent / "fixtures" / "protocol_cases.json").read_text(encoding="utf-8"))


def assert_no_sensitive_logs(records, sentinels):
    for record in records:
        if record.name.startswith("emtl"):
            fields = (record.msg, record.args, record.getMessage(), record.exc_info, record.exc_text, record.stack_info)
            for sentinel in sentinels:
                assert all(sentinel not in str(field) for field in fields)
