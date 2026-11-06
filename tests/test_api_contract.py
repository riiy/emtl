import inspect

import emtl
from emtl import core
from emtl import utils


def test_exports_and_signatures():
    names = [
        "login",
        "query_asset_and_position",
        "query_orders",
        "query_history_orders",
        "query_trades",
        "query_history_trades",
        "query_funds_flow",
        "create_order",
        "cancel_order",
    ]
    assert emtl.__all__ == names
    for name in names:
        assert getattr(emtl, name) is getattr(core, name)
    signatures = {
        "login": "(username: str = '', password: str = '', duration: int = 30) -> Optional[str]",
        "query_asset_and_position": "()",
        "query_orders": "()",
        "query_trades": "()",
        "query_history_orders": "(size, start_time, end_time)",
        "query_history_trades": "(size, start_time, end_time)",
        "query_funds_flow": "(size, start_time, end_time)",
        "create_order": "(stock_code, trade_type, market: str, price: float, amount: int)",
        "cancel_order": "(order_str: str)",
    }
    for name, signature in signatures.items():
        assert str(inspect.signature(getattr(emtl, name))) == signature
    assert str(inspect.signature(core.get_last_price)) == "(symbol_code: str, market: str) -> float"
    assert str(inspect.signature(utils.get_logger)) == "(name)"
    assert str(inspect.signature(utils.emt_trade_encrypt)) == "(content: str) -> str"
    assert str(inspect.signature(utils.double_equal)) == "(a, b) -> bool"
    assert str(inspect.signature(utils.get_float)) == "(data: dict, key: str) -> float"
    assert str(inspect.signature(utils.get_int)) == "(data: dict, key: str) -> int"
