import re
from random import SystemRandom
from typing import Any
from typing import Dict
from typing import Optional

from ddddocr import DdddOcr
from requests import Response
from requests import Session
from requests import get

from .const import _base_headers
from .const import _urls
from .utils import emt_trade_encrypt
from .utils import get_logger

logger = get_logger(__name__)
ocr = DdddOcr(show_ad=False)
session = Session()
_em_validate_key = ""


def _check_resp(resp: Response):
    if resp.status_code != 200:
        logger.error(f"request {resp.url} fail, code={resp.status_code}, response={resp.text}")
        raise


def _query_something(tag: str, req_data: Optional[dict] = None) -> Optional[Dict]:
    """通用查询函数

    :param tag: 请求类型
    :param req_data: 请求提交数据,可选
    :return:
    """
    assert _em_validate_key, "em_validatekey is empty"
    assert tag in _urls, f"{tag} not in url list"
    url = _urls[tag] + _em_validate_key
    if req_data is None:
        req_data = {
            "qqhs": 100,
            "dwc": "",
        }
    headers = _base_headers.copy()
    headers["X-Requested-With"] = "XMLHttpRequest"
    logger.debug(f"(tag={tag}), (data={req_data}), (url={url})")
    resp = session.post(url, headers=headers, data=req_data)
    _check_resp(resp)
    return resp.json()


def _get_captcha_code() -> tuple[float, Any]:
    """get random number and captcha code."""
    cryptogen = SystemRandom()
    random_num = cryptogen.random()
    resp = get(f"{_urls['yzm']}{random_num}", headers=_base_headers, timeout=60)
    _check_resp(resp)
    code = ocr.classification(resp.content)
    if code:
        try:
            code = int(code)
        except Exception as e:
            logger.error(f"get_captcha_code found exception: {e}, ocr result={code}")
            return _get_captcha_code()

    return random_num, code


def _get_em_validate_key():
    """获取 em_validatekey"""
    url = "https://jywg.18.cn/Trade/Buy"
    resp = session.get(url, headers=_base_headers)
    _check_resp(resp)
    match_result = re.findall(r'id="em_validatekey" type="hidden" value="(.*?)"', resp.text)
    if match_result:
        _em_validatekey = match_result[0].strip()
        global _em_validate_key
        _em_validate_key = _em_validatekey
        return _em_validatekey


def login(username: str, password: str, duration: int = 30) -> Optional[str]:
    """登录接口.

    :param str username: 用户名
    :param str password: 密码(明文)
    :param duration: 在线时长(分钟), defaults to 30
    :type duration: int, optional
    :return:
    """
    random_num, code = _get_captcha_code()
    headers = _base_headers.copy()
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Referer"] = "https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy"
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    url = _urls["login"]
    data = {
        "userId": username.strip(),
        "password": emt_trade_encrypt(password.strip()),
        "randNumber": random_num,
        "identifyCode": code,
        "duration": duration,
        "authCode": "",
        "type": "Z",
        "secInfo": "",
    }
    resp = session.post(url, headers=headers, data=data)
    _check_resp(resp)
    try:
        logger.info(f"login success for {resp.json()}")
        return _get_em_validate_key()
    except KeyError as e:
        logger.error(f"param data found exception:[{e}], [data={resp}]")


def query_asset_and_position():
    """Get asset and position."""
    resp = _query_something("query_asset_and_pos")
    if resp:
        return resp


def query_orders():
    """查询订单."""
    resp = _query_something("query_orders")
    if resp:
        return resp


def query_trades():
    """查询成交."""
    resp = _query_something("query_trades")
    if resp:
        return resp


def query_history_orders(size, start_time, end_time):
    """查询历史订单.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_his_orders", {"qqhs": size, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp


def query_history_trades(size, start_time, end_time):
    """查询历史成交.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_his_trades", {"qqhs": size, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp


def query_funds_flow(size, start_time, end_time):
    """查询资金.

    :param int size: 请求的数据的条目数
    :param str start_time: 起始时间, 格式"%Y-%m-%d"
    :param str end_time: 起始时间, 格式"%Y-%m-%d"
    :return dict:
    """
    resp = _query_something("query_funds_flow", {"qqhs": size, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp


def insert_order(stock_code, trade_type, market: str, price: float, amount: int):
    """交易接口, 买入或卖出.

    :param str stock_code: 股票代码
    :param str trade_type: 交易方向,B for buy, S for sell
    :param str market: 股票市场,HA 上海, SA
    :param float price: 股票价格
    :param int amount: 买入/卖出数量
    """
    req_data = {
        "stockCode": stock_code,
        "tradeType": trade_type,
        "zqmc": "",
        "market": market,
        "price": price,
        "amount": amount,
    }
    resp = _query_something("insert_order", req_data=req_data)
    logger.info(resp)
    if resp:
        return resp


def cancel_order(code: str):
    data = {"revokes": code.strip()}
    resp = _query_something("cancel_order", req_data=data)
    if resp:
        return resp
