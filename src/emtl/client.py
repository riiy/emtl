"""Synchronous, explicitly account-bound trading client."""

import os
import sys
from random import SystemRandom
from typing import Optional

from requests import Session

from . import _protocol
from ._coordination import account_entry
from ._coordination import claim
from ._coordination import release
from ._ocr import make_ocr
from .const import _base_headers
from .const import _urls
from .errors import BrokerHTTPError
from .errors import TradeOutcomeUnknown
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
            ocr = make_ocr() if self._ocr_factory is None else self._ocr_factory()
            claim(self, ocr)
            if not callable(getattr(ocr, "classification", None)):
                raise TypeError("invalid OCR dependency")
            self._ocr = ocr
        return self._ocr

    def _check_resp(self, resp, *, on_http_status=None):
        status = resp.status_code
        if type(status) is not int:  # noqa: E721 - exclude bool and untrusted subclasses.
            raise TypeError("invalid HTTP status") from None
        if status != 200:
            error = BrokerHTTPError(status)
            if on_http_status is not None:
                on_http_status(status)
            try:
                logger.error("request failed, code=%s", status)
            except Exception:  # noqa: S110 - preserve the safe HTTP error; never log handler exceptions.
                pass
            raise error from None

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

    def _query_something(self, tag, req_data=None, *, on_post_start=None, on_http_status=None):
        with self._account.lock:
            self._ensure_open()
            if self._state == "NEW":
                self.login()
            if self._state != "READY" or not self._token:
                raise RuntimeError("authentication required")
            check = self._check_resp
            if tag in {"create_order", "cancel_order"} and on_http_status is not None:

                def check(resp):
                    return self._check_resp(resp, on_http_status=on_http_status)

            return _protocol.query(
                self._session,
                self._token,
                tag,
                req_data,
                check,
                disable_order_redirects=True,
                on_post_start=on_post_start if tag in {"create_order", "cancel_order"} else None,
            )

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

    def _execute_trade(self, operation, data):
        attempted = False
        http_status = None

        def on_post_start():
            nonlocal attempted
            attempted = True

        def on_http_status(status):
            nonlocal http_status
            http_status = status

        try:
            resp = self._query_something(operation, req_data=data, on_post_start=on_post_start, on_http_status=on_http_status)
        except Exception:
            if not attempted:
                raise
            if http_status is not None:
                raise TradeOutcomeUnknown(operation, "http_status", http_status) from None
            raise TradeOutcomeUnknown(operation, "exchange_error") from None

        try:
            if operation == "create_order":
                return _protocol.order_result(resp, logger)
            return _protocol.cancel_result(resp)
        except Exception:
            if not attempted:
                raise
            raise TradeOutcomeUnknown(operation, "response_error") from None

    def create_order(self, stock_code, trade_type, market: str, price: float, amount: int):
        """Attempt one POST; ordinary post-boundary failures raise TradeOutcomeUnknown.

        This is not acceptance/execution evidence or permission to resubmit.
        Authentication and other pre-boundary failures are not trade unknowns.
        """
        with self._account.lock:
            data = _protocol.order_form(stock_code, trade_type, market, price, amount)
            return self._execute_trade("create_order", data)

    def cancel_order(self, order_str: str):
        """Attempt one revocation; post-boundary failures raise TradeOutcomeUnknown.

        Never automatically retry or interpret the returned text as execution.
        """
        with self._account.lock:
            self._ensure_open()
            return self._execute_trade("cancel_order", _protocol.cancel_form(order_str))

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
