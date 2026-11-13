import os
from random import SystemRandom
from typing import Any
from typing import Optional

from ._ocr import make_ocr
from requests import Response
from requests import Session
from requests import get

from . import _protocol
from .const import _urls
from .utils import emt_trade_encrypt
from .utils import get_logger

logger = get_logger(__name__)
ocr = make_ocr()
session = Session()
_em_validate_key = ""


def _query_snapshot(symbol_code: str, market: str) -> Optional[dict]:
    return _protocol.snapshot(session, symbol_code, market, _check_resp)


def get_last_price(symbol_code: str, market: str) -> float:
    return _protocol.last_price(_query_snapshot(symbol_code, market))


def _check_resp(resp: Response):
    return _protocol.check_response(resp, logger)


def _query_something(tag: str, req_data: Optional[dict] = None) -> Optional[Response]:
    """通用查询函数

    :param tag: 请求类型
    :param req_data: 请求提交数据,可选
    :return:
    """
    if not _em_validate_key:
        validate_key = login()
    else:
        validate_key = _em_validate_key
    return _protocol.query(session, validate_key, tag, req_data, _check_resp)


def _get_captcha_code() -> tuple[float, Any]:
    """get random number and captcha code."""
    return _protocol.captcha(get, lambda content: ocr.classification(content), SystemRandom, _check_resp, logger, _get_captcha_code)


def _get_em_validate_key():
    """获取 em_validatekey"""
    token = _protocol.fetch_token(session, _check_resp)
    if token is not None:
        global _em_validate_key
        _em_validate_key = token
        return token


def login(username: str = "", password: str = "", duration: int = 30) -> Optional[str]:
    """登录接口.

    :param str username: 用户名
    :param str password: 密码(明文)
    :param duration: 在线时长(分钟), defaults to 30
    :type duration: int, optional
    :return:
    """
    if not username:
        username = os.getenv("EM_USERNAME", "")
    if not password:
        password = os.getenv("EM_PASSWORD", "")
    random_num, code = _get_captcha_code()
    headers = _protocol.login_headers()
    url = _urls["login"]
    data = _protocol.login_form(username, password, duration, random_num, code, emt_trade_encrypt)
    resp = session.post(url, headers=headers, data=data)
    _check_resp(resp)
    try:
        _ = f"{resp.json()}"  # Preserve the original response parsing and formatting behavior.
        logger.info("authentication response received")
        return _get_em_validate_key()
    except KeyError:
        logger.error("authentication response processing failed")


def query_asset_and_position():
    """Get asset and position."""
    resp = _query_something("query_asset_and_pos")
    return _protocol.json_result(resp)


def query_orders():
    """查询订单."""
    resp = _query_something("query_orders")
    return _protocol.json_result(resp)


def query_trades():
    """查询成交."""
    resp = _query_something("query_trades")
    return _protocol.json_result(resp)


def query_history_orders(size, start_time, end_time):
    """查询历史订单.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_his_orders", _protocol.history_form(size, start_time, end_time))
    return _protocol.json_result(resp)


def query_history_trades(size, start_time, end_time):
    """查询历史成交.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_his_trades", _protocol.history_form(size, start_time, end_time))
    return _protocol.json_result(resp)


def query_funds_flow(size, start_time, end_time):
    """查询资金.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_funds_flow", _protocol.history_form(size, start_time, end_time))
    return _protocol.json_result(resp)


def create_order(stock_code, trade_type, market: str, price: float, amount: int):
    """交易接口, 买入或卖出.

    :param str stock_code: 股票代码
    :param str trade_type: 交易方向,B for buy, S for sell
    :param str market: 股票市场,HA 上海, SA
    :param float price: 股票价格
    :param int amount: 买入/卖出数量
    """
    req_data = _protocol.order_form(stock_code, trade_type, market, price, amount)
    resp = _query_something("create_order", req_data=req_data)
    return _protocol.order_result(resp, logger)


def cancel_order(order_str: str):
    """取消交易接口.

    :param str order_str: 订单字符串, 由成交日期+成交编号组成. 在create_order和query_order接口, Wtrq的值是成交日期, Wtbh的值是成交编号, 格式为: 20240520_130662
    """
    data = _protocol.cancel_form(order_str)
    resp = _query_something("cancel_order", req_data=data)
    return _protocol.cancel_result(resp)
