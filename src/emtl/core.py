import re
from random import SystemRandom
from typing import Any
from typing import Optional

from ddddocr import DdddOcr
from requests import Session
from requests import get

from .const import _base_headers
from .const import _urls
from .utils import emt_trade_encrypt
from .utils import get_logger
from .utils import response_deserialize

logger = get_logger(__name__)
ocr = DdddOcr(show_ad=False)
session = Session()


def emt(user, password):
    return user, password


def _get_captcha_code() -> Optional[tuple[float, Any]]:
    """get random number and captcha code."""
    cryptogen = SystemRandom()
    random_num = cryptogen.random()
    resp = get(f"https://jywg.18.cn/Login/YZM?randNum={random_num}", headers=_base_headers, timeout=60)
    if resp.status_code != 200:
        logger.error(f"get captcha code fail, code={resp.status_code}, response={resp.text}")
        return None
    code = ocr.classification(resp.content)
    logger.debug(f"random_num={random_num}, code={code}")
    if code:
        try:
            return random_num, int(code)
        except Exception as e:
            logger.error(f"get_captcha_code found exception: {e}, ocr result={code}")
            return _get_captcha_code()
    return None


def _get_em_validate_key():
    """获取 em_validatekey"""
    url = "https://jywg.18.cn/Trade/Buy"
    resp = session.get(url, headers=_base_headers)
    if resp.status_code != 200:
        logger.error(f"get em validatekey fail, code={resp.status_code}, response={resp.text}")
    logger.info(resp.text)
    match_result = re.findall(r'id="em_validatekey" type="hidden" value="(.*?)"', resp.text)
    if match_result:
        _em_validatekey = match_result[0].strip()
        logger.debug(f"success to get em_validatekey={_em_validatekey}")
        return _em_validatekey
    return ""


def login(username: str, password: str, duration: int = 30) -> str:
    """Login.
    :param username: 用户名
    :param password: 密码(明文)
    :param duration: 在线时长(分钟)
    :return:
    """
    if (ret := _get_captcha_code()) is None:
        return ""
    random_num, code = ret
    logger.error(code)
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
    if resp.status_code != 200:
        logger.error(f"user [{username}] login fail, code={resp.status_code}, response={resp.text}")
        return ""

    data = resp.json()
    try:
        resp = response_deserialize(data)
        if resp and resp.status == 0 and resp.message.strip() == "":
            logger.info(f"login success for {resp.data[0]['khmc']}({username})")
            return _get_em_validate_key()
    except KeyError as e:
        logger.error(f"param data found exception:[{e}], [data={data}]")
        return ""
    return ""
