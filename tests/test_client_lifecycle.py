import gc
import weakref
from threading import Barrier
from threading import Event
from unittest.mock import Mock

import pytest

from emtl import _coordination
from emtl import client as client_module
from emtl.client import TradingClient
from tests.client_helpers import WAIT
from tests.client_helpers import ObservedLock
from tests.client_helpers import Workers
from tests.client_helpers import fake_session
from tests.client_helpers import ready
from tests.helpers import response


@pytest.mark.parametrize(
    ("username", "password", "error"),
    [(None, "fake", TypeError), (" ", "fake", ValueError), ("fake", 1, TypeError), ("fake", " ", ValueError), ("fake", None, ValueError)],
)
def test_invalid_credentials_do_not_create_resources(username, password, error):
    factory = Mock()
    with pytest.raises(error):
        TradingClient(username, password, session_factory=factory)
    factory.assert_not_called()


def test_environment_password_snapshot_and_identity(monkeypatch):
    monkeypatch.setenv("EM_USERNAME", "P2_FAKE_IGNORED")
    monkeypatch.setenv("EM_PASSWORD", " P2_FAKE_PASSWORD ")
    a = TradingClient(" 001A ", session_factory=fake_session)
    b = TradingClient("001A", "other", session_factory=fake_session)
    c = TradingClient("001a", "other", session_factory=fake_session)
    d = TradingClient("1A", "other", session_factory=fake_session)
    try:
        monkeypatch.setenv("EM_PASSWORD", "P2_FAKE_CHANGED")
        assert a._username == "001A"
        expected = "P2_FAKE_PASSWORD"
        assert a._password == expected
        assert a._account is b._account
        assert a._account is not c._account
        assert a._account is not d._account
        assert a._session is not b._session
        assert a._session.cookies is not b._session.cookies
        for value in (a._username, a._password):
            assert value not in repr(a)
    finally:
        for client in (a, b, c, d):
            client.close()


def test_default_constructor_does_not_call_http_or_ocr(monkeypatch):
    ocr = Mock(side_effect=AssertionError("OCR must be lazy"))
    monkeypatch.setattr(client_module, "make_ocr", ocr
    client = TradingClient("P2_FAKE_A", "P2_FAKE_PASSWORD")
    session = client._session
    assert not session.cookies
    assert client._token == ""
    assert client._state == "NEW"
    assert session.get_adapter("https://").max_retries.total == 0
    ocr.assert_not_called()
    client.close()
    client.close()
    with pytest.raises(RuntimeError, match="client is closed"):
        client.query_orders()


def test_reused_session_or_cookie_jar_is_rejected_without_harming_owner():
    session = fake_session()
    owner = TradingClient("P2_FAKE_A", "fake", session_factory=lambda: session)
    session.cookies.set("p2", "P2_FAKE_COOKIE")
    try:
        with pytest.raises(ValueError, match="already in use"):
            TradingClient("P2_FAKE_B", "fake", session_factory=lambda: session)
        session.close.assert_not_called()
        assert session.cookies.get("p2") == "P2_FAKE_COOKIE"
        other = fake_session()
        other.cookies = session.cookies
        with pytest.raises(ValueError, match="already in use"):
            TradingClient("P2_FAKE_B", "fake", session_factory=lambda: other)
        other.close.assert_called_once()
        session.close.assert_not_called()
        assert session.cookies.get("p2") == "P2_FAKE_COOKIE"
    finally:
        owner.close()


def test_ocr_is_lazy_independent_and_shared_ocr_is_rejected():
    ocr = Mock()
    factory = Mock(return_value=ocr)
    a = TradingClient("P2_FAKE_A", "fake", session_factory=fake_session, ocr_factory=factory)
    b = TradingClient("P2_FAKE_B", "fake", session_factory=fake_session, ocr_factory=factory)
    try:
        factory.assert_not_called()
        with a._account.lock:
            assert a._get_ocr() is a._get_ocr() is ocr
        factory.assert_called_once()
        with b._account.lock, pytest.raises(ValueError, match="already in use"):
            b._get_ocr()
        assert a._ocr is ocr
        assert b._ocr is None
    finally:
        a.close()
        b.close()


def test_close_failure_is_final_and_releases_registration():
    session = fake_session()
    error = ValueError("P2_FAKE_CLOSE")
    session.close.side_effect = error
    client = ready(TradingClient("P2_FAKE_A", "fake", session_factory=lambda: session))
    session.cookies.set("p2", "P2_FAKE_COOKIE")
    with pytest.raises(ValueError, match="P2_FAKE_CLOSE") as caught:
        client.close()
    assert caught.value is error
    client.close()
    assert not session.cookies
    assert client._token == client._password == ""
    assert client._state == "CLOSED"
    assert not client._owned_resources
    assert id(session) not in _coordination._owners
    session.close.assert_called_once()


def test_close_waits_for_response_processing(monkeypatch):
    entered, release = Event(), Event()
    session = fake_session()
    reply = response({})

    def decode():
        entered.set()
        assert release.wait(WAIT)
        return "P2_FAKE_RESULT"

    reply.json = decode
    session.post.return_value = reply
    client = ready(TradingClient("P2_FAKE_A", "fake", session_factory=lambda: session))
    observed = ObservedLock(client._account.lock)
    monkeypatch.setattr(client._account, "lock", observed)
    workers = Workers()
    try:
        workers.start(client.query_orders)
        assert entered.wait(WAIT)
        workers.start(client.close)
        assert observed.contended.wait(WAIT)
        session.close.assert_not_called()
    finally:
        release.set()
        results = workers.finish()
        client.close()
    assert "P2_FAKE_RESULT" in results
    session.close.assert_called_once()


def test_closed_instance_keeps_same_account_entry_until_garbage_collected():
    a = TradingClient("P2_FAKE_GC", "fake", session_factory=fake_session)
    entry_ref = weakref.ref(a._account)
    resource_ids = [id(resource) for resource in a._owned_resources]
    a.close()
    b = TradingClient("P2_FAKE_GC", "fake", session_factory=fake_session)
    assert a._account is b._account
    b.close()
    del a, b
    gc.collect()
    assert entry_ref() is None
    assert "P2_FAKE_GC" not in _coordination._accounts
    assert not any(key in _coordination._owners for key in resource_ids)


def test_first_concurrent_construction_uses_one_entry():
    barrier = Barrier(2)
    workers = Workers()

    def construct():
        barrier.wait(WAIT)
        return TradingClient("P2_FAKE_CONCURRENT", "fake", session_factory=fake_session)

    for _ in range(2):
        workers.start(construct)
    clients = workers.finish()
    try:
        assert clients[0]._account is clients[1]._account
    finally:
        for client in clients:
            client.close()


def test_closed_client_blocks_every_public_operation(client_factory):
    client = ready(client_factory())
    session = client._session
    client.close()
    client.close()
    operations = [
        client.login,
        client.query_asset_and_position,
        client.query_orders,
        client.query_trades,
        lambda: client.query_history_orders(1, "start", "end"),
        lambda: client.query_history_trades(1, "start", "end"),
        lambda: client.query_funds_flow(1, "start", "end"),
        lambda: client.create_order("FAKE", "B", "SA", 1, 100),
        lambda: client.cancel_order("FAKE"),
        lambda: client.get_last_price("FAKE", "SA"),
    ]
    for operation in operations:
        with pytest.raises(RuntimeError, match="^client is closed$"):
            operation()
    session.post.assert_not_called()
    session.get.assert_not_called()
    session.close.assert_called_once()


def test_unique_account_registry_does_not_retain_history():
    references = []
    for index in range(30):
        client = TradingClient(f"P2_FAKE_HISTORY_{index}", "fake", session_factory=fake_session)
        references.append(weakref.ref(client._account))
        client.close()
    del client
    gc.collect()
    assert all(ref() is None for ref in references)
    assert not any(key.startswith("P2_FAKE_HISTORY_") for key in _coordination._accounts)


def test_construction_failure_releases_new_session_but_preserves_primary_error():
    session = fake_session()
    session.cookies = object()
    session.close.side_effect = ValueError("P2_FAKE_CLOSE")
    with pytest.raises(TypeError, match="invalid cookie dependency"):
        TradingClient("P2_FAKE_A", "fake", session_factory=lambda: session)
    session.close.assert_called_once()
    assert id(session) not in _coordination._owners


def test_cookie_cleanup_error_still_closes_client(client_factory, monkeypatch):
    client = ready(client_factory())
    session = client._session
    error = ValueError("P2_FAKE_CLEAR")
    monkeypatch.setattr(session.cookies, "clear", Mock(side_effect=error))
    session.close.side_effect = RuntimeError("P2_FAKE_SECONDARY")
    with pytest.raises(ValueError, match="P2_FAKE_CLEAR") as caught:
        client.close()
    assert caught.value is error
    assert client._state == "CLOSED"
    assert client._password == client._token == ""
    client.close()
    session.close.assert_called_once()
