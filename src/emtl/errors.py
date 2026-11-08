"""Safe, minimal error signals for the explicit TradingClient only."""

from typing import Optional


class BrokerHTTPError(RuntimeError):
    """A non-trading response has an integer HTTP status other than 200."""

    def __init__(self, status_code: int):
        if type(status_code) is not int:  # noqa: E721 - reject bool and untrusted subclasses.
            raise TypeError("invalid HTTP status") from None
        if status_code == 200:
            raise ValueError("HTTP status must not be 200") from None
        self.status_code = status_code
        super().__init__(f"broker HTTP status {status_code}")


class TradeOutcomeUnknown(RuntimeError):
    """A trade POST was attempted; never use this signal to resubmit automatically.

    The safe fields describe a local failure stage, not broker acceptance or
    execution. Original transport/response exceptions are not public fields.
    """

    def __init__(self, operation: str, reason: str, status_code: Optional[int] = None):
        if type(operation) is not str or type(reason) is not str:  # noqa: E721 - exact builtins only.
            raise TypeError("invalid trade error fields") from None
        if operation not in {"create_order", "cancel_order"} or reason not in {"exchange_error", "http_status", "response_error"}:
            raise ValueError("invalid trade error fields") from None
        if reason == "http_status":
            if type(status_code) is not int:  # noqa: E721 - exclude bool and untrusted subclasses.
                raise TypeError("invalid HTTP status") from None
            if status_code == 200:
                raise ValueError("HTTP status must not be 200") from None
        elif status_code is not None:
            raise ValueError("status is only valid for http_status") from None
        self.operation = operation
        self.reason = reason
        self.status_code = status_code
        status = "" if status_code is None else f", status_code={status_code}"
        super().__init__(f"trade outcome unknown: operation={operation}, reason={reason}{status}; do not automatically resubmit")
