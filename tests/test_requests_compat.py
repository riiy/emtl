"""Requests 2.33.1 compatibility without relaxing the P0 test network guard.

Session.request and Session.send are intentionally blocked by tests/_offline.py.
Use only Requests' offline preparation API plus a synthetic protocol transport.
"""

from importlib.metadata import version

from requests import Request
from requests import Response
from requests import Session

from emtl import _protocol


def test_approved_requests_runtime_version():
    assert version("requests") == "2.33.1"


def test_session_still_defaults_to_tls_verification():
    with Session() as session:
        assert session.verify is True


def test_requests_can_prepare_trade_form_without_sending():
    """Exercise real Requests encoding without calling guarded request/send."""
    with Session() as session:
        session.trust_env = False  # no proxy or .netrc inputs
        prepared = session.prepare_request(
            Request("POST", "https://example.invalid/order", data={"stockCode": "SYNTHETIC"})
        )
    assert prepared.method == "POST"
    assert prepared.url == "https://example.invalid/order"
    assert prepared.body == "stockCode=SYNTHETIC"


def test_trade_query_does_not_request_an_automatic_redirect_or_retry():
    """A synthetic 302 never triggers a second trade POST."""
    calls = []

    class SyntheticSession:
        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            response = Response()
            response.status_code = 302
            response.url = url
            response.headers["Location"] = "https://example.invalid/redirect-target"
            response._content = b"synthetic redirect"
            return response

    starts = []
    fake_token = "SYNTHETIC_VALIDATE_KEY"
    response = _protocol.query(
        SyntheticSession(),
        token=fake_token,
        tag="create_order",
        req_data={"stockCode": "SYNTHETIC"},
        check=lambda result: None,
        disable_order_redirects=True,
        on_post_start=lambda: starts.append("started"),
    )
    assert starts == ["started"]
    assert response.status_code == 302
    assert len(calls) == 1
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][1]["data"] == {"stockCode": "SYNTHETIC"}
