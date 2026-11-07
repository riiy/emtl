"""Synchronous, explicitly account-bound trading client."""

import os
import sys
from random import SystemRandom
from typing import Optional

from ddddocr import DdddOcr
from requests import Session

from . import _protocol
from ._coordination import account_entry
from ._coordination import claim
from ._coordination import release
from .const import _base_headers
from .const import _urls
from .utils import emt_trade_encrypt
from .utils import get_logger

logger = get_logger(__name__)


class TradingClient:
    """Own one account identity and one independent HTTP session."""

    def __init__(self, username: str, password: Optional[str] = None, *, session_factory=None, ocr_factory=None):
        if not isinstance(username, str):
            raise TypeError("username must be a string")
        username = username.strip()
        if not username:
            raise ValueError("username is required")
        if password is None:
            password = os.getenv("EM_PASSWORD", "")
        if not isinstance(password, str):
            raise TypeError("password must be a string")
        if not password.strip():
            raise ValueError("password is required")
        self._username = username
        self._password = password.strip()
        self._account = account_entry(username)
        self._session = None
        self._owned_resources = []
        self._ocr = None
        self._ocr_factory = ocr_factory
        self._token = ""
        self._state = "NEW"
        session = (Session if session_factory is None else session_factory)()
        try:
            claim(self, session)
            self._session = session
            if not all(callable(getattr(session, name, None)) for name in ("get", "post", "close")):
                raise TypeError("invalid session dependency")
            cookies = session.cookies
            if not callable(getattr(cookies, "clear", None)):
                raise TypeError("invalid cookie dependency")
            claim(self, cookies)
        except BaseException:
            try:
                if self._session is not None and callable(getattr(session, "close", None)):
                    self._close_session(preserve_error=True)
            finally:
                self._state = "CLOSED"
                self._password = ""
                release(self)
                self._session = None
            raise

    def _close_session(self, *, preserve_error=False):
        try:
            self._session.close()
        except BaseException:
            if not preserve_error:
                raise

    def _clear_cookies(self, *, preserve_error=False):
        try:
            self._session.cookies.clear()
        except BaseException:
            if not preserve_error:
                raise

    def _ensure_open(self):
        if self._state == "CLOSED":
            raise RuntimeError("client is closed")

    def _get_ocr(self):
        if self._ocr is None:
            ocr = DdddOcr(show_ad=False) if self._ocr_factory is None else self._ocr_factory()
            claim(self, ocr)
            if not callable(getattr(ocr, "classification", None)):
                raise TypeError("invalid OCR dependency")
            self._ocr = ocr
        return self._ocr

    def _check_resp(self, resp):
        return _protocol.check_response(resp, logger)

    def _get_captcha_code(self):
        return _protocol.captcha(
            self._session.get,
            lambda content: self._get_ocr().classification(content),
            SystemRandom,
            self._check_resp,
            logger,
            self._get_captcha_code,
            headers=_base_headers.copy(),
        )

    def login(self, duration: int = 30) -> Optional[str]:
        """Authenticate afresh; insufficient evidence returns None, never old state.

        Status=0 is a conservative local gate, not a verified broker protocol.
        Transport/decoding errors propagate after invalidating authentication.
        """
        with self._account.lock:
            self._ensure_open()
            self._token = ""
            self._state = "AUTHENTICATING"
            success = False
            try:
                self._session.cookies.clear()
                random_num, code = self._get_captcha_code()
                data = _protocol.login_form(self._username, self._password, duration, random_num, code, emt_trade_encrypt)
                resp = self._session.post(_urls["login"], headers=_protocol.login_headers(), data=data)
                self._check_resp(resp)
                payload = resp.json()
                if (
                    not isinstance(payload, dict)
                    or type(payload.get("Status")) is not int  # noqa: E721 - approved gate excludes bool and float.
                    or payload["Status"] != 0
                ):
                    return None
                token = _protocol.fetch_token(self._session, self._check_resp, headers=_base_headers.copy())
                if not token:
                    return None
                self._token = token
                self._state = "READY"
                logger.info("authentication response received")
                success = True
                return token
            finally:
                if not success:
                    self._token = ""
                    self._state = "FAILED"
                    self._clear_cookies(preserve_error=sys.exc_info()[0] is not None)

    def _query_something(self, tag, req_data=None):
        with self._account.lock:
            self._ensure_open()
            if self._state == "NEW":
                self.login()
            if self._state != "READY" or not self._token:
                raise RuntimeError("authentication required")
            return _protocol.query(self._session, self._token, tag, req_data, self._check_resp, disable_order_redirects=True)

    def query_asset_and_position(self):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_asset_and_pos"))

    def query_orders(self):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_orders"))

    def query_trades(self):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_trades"))

    def query_history_orders(self, size, start_time, end_time):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_his_orders", _protocol.history_form(size, start_time, end_time)))

    def query_history_trades(self, size, start_time, end_time):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_his_trades", _protocol.history_form(size, start_time, end_time)))

    def query_funds_flow(self, size, start_time, end_time):
        with self._account.lock:
            return _protocol.json_result(self._query_something("query_funds_flow", _protocol.history_form(size, start_time, end_time)))

    def create_order(self, stock_code, trade_type, market: str, price: float, amount: int):
        """Attempt one submission; an exception can mean the result is unknown."""
        with self._account.lock:
            data = _protocol.order_form(stock_code, trade_type, market, price, amount)
            return _protocol.order_result(self._query_something("create_order", req_data=data), logger)

    def cancel_order(self, order_str: str):
        """Attempt one revocation, without retrying or interpreting its text."""
        with self._account.lock:
            self._ensure_open()
            return _protocol.cancel_result(self._query_something("cancel_order", req_data=_protocol.cancel_form(order_str)))

    def get_last_price(self, symbol_code: str, market: str) -> float:
        with self._account.lock:
            self._ensure_open()
            return _protocol.last_price(_protocol.snapshot(self._session, symbol_code, market, self._check_resp))

    def close(self) -> None:
        with self._account.lock:
            if self._state == "CLOSED":
                return
            self._state = "CLOSED"
            self._token = ""
            self._password = ""
            try:
                self._session.cookies.clear()
            finally:
                try:
                    self._close_session(preserve_error=sys.exc_info()[0] is not None)
                finally:
                    release(self)
                    self._session = None
                    self._ocr = None
                    self._ocr_factory = None
