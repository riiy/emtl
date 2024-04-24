import re
from random import SystemRandom
from typing import Any
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


def emt(user, password):
    return user, password


def _check_resp(resp: Response):
    if resp.status_code != 200:
        logger.error(f"request {resp.url} fail, code={resp.status_code}, response={resp.text}")
        raise


def _query_something(tag: str, data: Optional[dict] = None) -> Optional[Response]:
    """通用查询函数

    :param tag: 请求类型
    :param count: 查询数量,可选
    :param data: 请求提交数据,可选
    :return:
    """
    assert _em_validate_key, "em_validatekey is empty"
    assert tag in _urls, f"{tag} not in url list"
    url = _urls[tag] + _em_validate_key
    if data is None:
        data = {
            "qqhs": 100,
            "dwc": "",
        }
    headers = _base_headers.copy()
    headers["X-Requested-With"] = "XMLHttpRequest"
    logger.debug(f"(tag={tag}), (data={data}), (url={url})")
    resp = session.post(url, headers=headers, data=data)
    _check_resp(resp)
    return resp


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
        return resp.json()


def query_orders():
    resp = _query_something("query_orders")
    if resp:
        return resp.json()


def query_trades():
    resp = _query_something("query_trades")
    if resp:
        return resp.json()


def query_history_orders(count, start_time, end_time):
    resp = _query_something("query_his_orders", {"qqhs": count, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp.json()


def query_history_trades(count, start_time, end_time):
    resp = _query_something("query_his_trades", {"qqhs": count, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp.json()


def query_funds_flow(count, start_time, end_time):
    resp = _query_something("query_funds_flow", {"qqhs": count, "dwc": "", "st": start_time, "et": end_time})
    if resp:
        return resp.json()
