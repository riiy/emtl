"""Stateless protocol details shared by the client and legacy adapters."""

import re

from .const import _base_headers
from .const import _urls
from .utils import get_float


def check_response(resp, logger):
    if resp.status_code != 200:
        logger.error("request failed, code=%s", resp.status_code)
        raise


def query(session, token, tag, req_data, check, *, disable_order_redirects=False):
    assert tag in _urls, f"{tag} not in url list"
    url = _urls[tag] + token
    if req_data is None:
        req_data = {"qqhs": 100, "dwc": ""}
    headers = _base_headers.copy()
    headers["X-Requested-With"] = "XMLHttpRequest"
    options = {"allow_redirects": False} if disable_order_redirects and tag in {"create_order", "cancel_order"} else {}
    resp = session.post(url, headers=headers, data=req_data, **options)
    check(resp)
    return resp


def captcha(get_image, classify, random_factory, check, logger, retry, *, headers=None):
    random_num = random_factory().random()
    resp = get_image(f"{_urls['yzm']}{random_num}", headers=_base_headers if headers is None else headers, timeout=60)
    check(resp)
    code = classify(resp.content)
    if code:
        try:
            code = int(code)
        except Exception:
            logger.error("captcha recognition failed")
            return retry()
    return random_num, code


def login_headers():
    headers = _base_headers.copy()
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Referer"] = "https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy"
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    return headers


def login_form(username, password, duration, random_num, code, encrypt):
    return {
        "userId": username.strip(),
        "password": encrypt(password.strip()),
        "randNumber": random_num,
        "identifyCode": code,
        "duration": duration,
        "authCode": "",
        "type": "Z",
        "secInfo": "",
    }


def fetch_token(session, check, *, headers=None):
    resp = session.get("https://jywg.18.cn/Trade/Buy", headers=_base_headers if headers is None else headers)
    check(resp)
    matches = re.findall(r'id="em_validatekey" type="hidden" value="(.*?)"', resp.text)
    if matches:
        return matches[0].strip()


def history_form(size, start_time, end_time):
    return {"qqhs": size, "dwc": "", "st": start_time, "et": end_time}


def order_form(stock_code, trade_type, market, price, amount):
    return {"stockCode": stock_code, "tradeType": trade_type, "zqmc": "", "market": market, "price": price, "amount": amount}


def cancel_form(order_str):
    return {"revokes": order_str.strip()}


def json_result(resp):
    if resp:
        return resp.json()


def order_result(resp, logger):
    if resp:
        resp.json()  # Preserve both evaluations and return the second object.
        logger.info("order response received")
        return resp.json()


def cancel_result(resp):
    if resp:
        return resp.text.strip()


def snapshot(session, symbol_code, market, check):
    resp = session.get(
        "https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot",
        params={"id": symbol_code.strip(), "market": market},
        headers=_base_headers.copy(),
    )
    check(resp)
    return resp.json()


def last_price(ret):
    if ret is None or "status" not in ret or ret["status"] != 0:
        return float("nan")
    return get_float(ret["realtimequote"], "currentPrice")
