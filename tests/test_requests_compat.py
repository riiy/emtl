"""Verify the upgraded Requests runtime without reaching a broker or network.

The adapter is an in-memory transport; no live trading, login or real secrets.
"""

from importlib.metadata import version

from requests import Response
from requests import Session
from requests.adapters import BaseAdapter

from emtl import _protocol


class RecordingAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append((request, kwargs))
        response = Response()
        response.status_code = 302
        response.url = request.url
        response.request = request
        response.headers["Location"] = "https://example.invalid/redirect-target"
        response._content = b"synthetic redirect"
        return response

    def close(self):
        pass


def test_approved_requests_runtime_version():
    assert version("requests") == "2.33.1"


def test_session_still_defaults_to_tls_verification():
    with Session() as session:
        assert session.verify is True


def test_real_requests_session_does_not_follow_trade_post_redirect():
    """An order POST must never become an automatic second HTTP request."""
    adapter = RecordingAdapter()
    starts = []
    with Session() as session:
        session.trust_env = False  # isolate CI from host proxies and .netrc
        session.mount("https://", adapter)
        response = _protocol.query(
            session,
            token="synthetic",
            tag="create_order",
            req_data={"stockCode": "SYNTHETIC"},
            check=lambda result: None,
            disable_order_redirects=True,
            on_post_start=lambda: starts.append("started"),
        )
    assert starts == ["started"]
    assert response.status_code == 302
    assert len(adapter.requests) == 1
    request, kwargs = adapter.requests[0]
    assert request.method == "POST"
    assert b"stockCode=SYNTHETIC" in request.body
    assert kwargs["verify"] is True
    assert "redirect-target" not in request.url
