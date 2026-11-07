from unittest.mock import Mock

import pytest
from requests import Response

from emtl import core


class UnexpectedCalls:
    def __getattr__(self, name):
        raise RuntimeError("unconfigured test HTTP")


def unexpected(*args, **kwargs):
    raise RuntimeError("unconfigured test HTTP")


@pytest.fixture(autouse=True)
def _isolated_core(monkeypatch):
    monkeypatch.setattr(core, "session", UnexpectedCalls())
    monkeypatch.setattr(core, "get", unexpected)
    monkeypatch.setattr(core, "ocr", UnexpectedCalls())
    monkeypatch.setattr(core, "_em_validate_key", "")
    monkeypatch.delenv("EM_USERNAME", raising=False)
    monkeypatch.delenv("EM_PASSWORD", raising=False)


@pytest.fixture
def fake_captcha(monkeypatch):
    image = Response()
    image.status_code = 200
    image._content = b"P0_FAKE_IMAGE"
    monkeypatch.setattr(core, "SystemRandom", Mock(return_value=Mock(random=Mock(return_value=0.5))))
    monkeypatch.setattr(core, "get", Mock(return_value=image))
    monkeypatch.setattr(core, "ocr", Mock(classification=Mock(return_value="1234")))
    return core.ocr


@pytest.fixture
def client_factory():
    from emtl.client import TradingClient
    from tests.client_helpers import fake_session

    clients = []
    synthetic = "P2_FAKE_PASSWORD"

    def create(username="P2_FAKE_A", password=synthetic, *, session=None, ocr=None):
        session = fake_session() if session is None else session
        ocr = Mock(classification=Mock(return_value="1234")) if ocr is None else ocr
        client = TradingClient(username, password, session_factory=lambda: session, ocr_factory=lambda: ocr)
        clients.append(client)
        return client

    yield create
    for client in clients:
        client.close()
