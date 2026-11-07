"""P2 Kill Tests: actual public request paths, no sleeps or live transport."""

from threading import Barrier
from threading import Event

import pytest

from emtl import core
from emtl.client import TradingClient
from emtl.const import _urls
from tests.client_helpers import WAIT
from tests.client_helpers import ObservedLock
from tests.client_helpers import Workers
from tests.client_helpers import fake_session
from tests.client_helpers import memory_session
from tests.client_helpers import ready
from tests.client_helpers import token_reply
from tests.helpers import response


@pytest.mark.parametrize("stage", ["post", "json"])
def test_kill_same_account_serializes_across_instances(stage, monkeypatch):
    first_entered, release_first, second_entered = Event(), Event(), Event()
    sessions = [fake_session(), fake_session()]
    clients = [
        TradingClient(name, "P2_FAKE_PASSWORD", session_factory=lambda s=s: s) for name, s in zip((" P2_FAKE_A ", "P2_FAKE_A"), sessions)
    ]
    for client in clients:
        ready(client)
    assert clients[0]._account is clients[1]._account
    observed = ObservedLock(clients[0]._account.lock)
    monkeypatch.setattr(clients[0]._account, "lock", observed)

    def block():
        first_entered.set()
        assert release_first.wait(WAIT), "first request not released"
        return ["first"]

    def first_post(*args, **kwargs):
        reply = response(["first"])
        if stage == "post":
            block()
        else:
            reply.json = block
        return reply

    def second_post(*args, **kwargs):
        second_entered.set()
        return response(["second"])

    sessions[0].post.side_effect = first_post
    sessions[1].post.side_effect = second_post
    workers = Workers()
    try:
        workers.start(clients[0].query_orders)
        assert first_entered.wait(WAIT)
        workers.start(clients[1].query_orders)
        assert observed.contended.wait(WAIT), "no evidence that second operation attempted the account lock"
        assert not second_entered.is_set()
    finally:
        release_first.set()
        try:
            results = workers.finish()
        finally:
            for client in clients:
                client.close()
    assert sorted(results) == [["first"], ["second"]]
    assert second_entered.is_set()
    for session in sessions:
        session.post.assert_called_once()


def test_kill_different_accounts_enter_http_together():
    barrier = Barrier(2)
    entered = [Event(), Event()]
    release = Event()
    sessions = [fake_session(), fake_session()]
    clients = [
        ready(TradingClient(name, "P2_FAKE_PASSWORD", session_factory=lambda s=s: s))
        for name, s in zip(("P2_FAKE_A", "P2_FAKE_B"), sessions)
    ]
    assert clients[0]._account is not clients[1]._account

    def post(index):
        def invoke(*args, **kwargs):
            entered[index].set()
            barrier.wait(WAIT)
            assert release.wait(WAIT)
            return response([index])

        return invoke

    for index, session in enumerate(sessions):
        session.post.side_effect = post(index)
    workers = Workers()
    try:
        for client in clients:
            workers.start(client.query_orders)
        assert all(event.wait(WAIT) for event in entered)
        assert all(thread.is_alive() for thread in workers.threads)
    finally:
        release.set()
        try:
            results = workers.finish()
        finally:
            for client in clients:
                client.close()
    assert sorted(results) == [[0], [1]]


def test_kill_sessions_tokens_and_prepared_cookies_never_cross():
    barrier = Barrier(2)
    before = core.session, core._em_validate_key, core.ocr
    clients, adapters = [], []

    def handler(request):
        barrier.wait(WAIT)
        return response(request.headers["X-P2-Account"])

    for account in ("A", "B"):
        session, adapter = memory_session(handler)
        session.cookies.set("p2_session", f"P2_FAKE_COOKIE_{account}", domain="jywg.18.cn", path="/")
        session.headers.update({"X-P2-Account": account, "Authorization": f"P2_FAKE_AUTH_{account}"})
        clients.append(
            ready(TradingClient(f"P2_FAKE_{account}", "P2_FAKE_PASSWORD", session_factory=lambda s=session: s), f"P2_FAKE_TOKEN_{account}")
        )
        adapters.append(adapter)
    assert clients[0]._session is not clients[1]._session
    assert clients[0]._session.cookies is not clients[1]._session.cookies
    workers = Workers()
    try:
        for client in clients:
            workers.start(client.query_orders)
        assert sorted(workers.finish()) == ["A", "B"]
        for account, adapter in zip(("A", "B"), adapters):
            assert len(adapter.requests) == 1
            request = adapter.requests[0]
            assert request.url.endswith(f"P2_FAKE_TOKEN_{account}")
            assert request.headers["Cookie"] == f"p2_session=P2_FAKE_COOKIE_{account}"
            assert request.headers["Authorization"] == f"P2_FAKE_AUTH_{account}"
            other = "B" if account == "A" else "A"
            assert f"P2_FAKE_TOKEN_{other}" not in request.url
            assert f"P2_FAKE_COOKIE_{other}" not in str(request.headers)
        assert (core.session, core._em_validate_key, core.ocr) == before
    finally:
        for client in clients:
            client.close()


@pytest.mark.parametrize(
    ("first", "second"),
    [("login", "query_orders"), ("login", "create_order"), ("create_order", "cancel_order"), ("query_orders", "query_orders")],
)
def test_same_account_serializes_mixed_operations(client_factory, monkeypatch, first, second):
    entered, release, second_sent = Event(), Event(), Event()
    a = ready(client_factory())
    b = a if first == second else ready(client_factory())
    original = a._account.lock
    observed = ObservedLock(original)
    monkeypatch.setattr(a._account, "lock", observed)
    workers = Workers()

    def post(*args, **kwargs):
        if not entered.is_set():
            entered.set()
            assert release.wait(WAIT)
        else:
            second_sent.set()
        return response({"Status": 0})

    a._session.post.side_effect = post
    if b is not a:
        b._session.post.side_effect = post
    a._session.get.side_effect = [response(text="P2_FAKE_IMAGE"), token_reply()]

    def invoke(client, name):
        args = {"create_order": ("FAKE", "B", "SA", 1, 100), "cancel_order": ("FAKE",)}.get(name, ())
        return getattr(client, name)(*args)

    try:
        workers.start(lambda: invoke(a, first))
        assert entered.wait(WAIT)
        workers.start(lambda: invoke(b, second))
        assert observed.contended.wait(WAIT)
        assert not second_sent.is_set()
    finally:
        release.set()
        workers.finish()
    assert second_sent.is_set()


def test_full_authentication_and_order_chains_never_cross_accounts(client_factory):
    barrier = Barrier(2)
    clients, adapters, ocrs = [], [], []
    old_state = core.session, core._em_validate_key, core.ocr

    def setup(account):
        session = None

        def handler(request):
            if request.url.startswith(_urls["yzm"]):
                assert "Cookie" not in request.headers
                barrier.wait(WAIT)
                session.cookies.set("p2_session", f"P2_FAKE_COOKIE_{account}", domain="jywg.18.cn", path="/")
                return response(text="P2_FAKE_IMAGE")
            assert request.headers["Cookie"] == f"p2_session=P2_FAKE_COOKIE_{account}"
            if request.url == _urls["login"]:
                return response({"Status": 0})
            if request.url == "https://jywg.18.cn/Trade/Buy":
                return token_reply(f"P2_FAKE_TOKEN_{account}")
            assert request.url.endswith(f"P2_FAKE_TOKEN_{account}")
            return response(text=f" {account} ") if request.url.startswith(_urls["cancel_order"]) else response([account])

        session, adapter = memory_session(handler)
        client = client_factory(f"P2_FAKE_{account}", session=session)
        clients.append(client)
        adapters.append(adapter)

    for account in ("A", "B"):
        setup(account)
    workers = Workers()

    def chain(client):
        token = client.login()
        ocrs.append(client._ocr)
        return token, client.query_orders(), client.create_order("FAKE", "B", "SA", 1, 100), client.cancel_order("FAKE")

    for client in clients:
        workers.start(lambda c=client: chain(c))
    results = workers.finish()
    assert sorted(results) == [("P2_FAKE_TOKEN_A", ["A"], ["A"], "A"), ("P2_FAKE_TOKEN_B", ["B"], ["B"], "B")]
    assert ocrs[0] is not ocrs[1]
    for account, adapter in zip(("A", "B"), adapters):
        assert len(adapter.requests) == 6
        other = "B" if account == "A" else "A"
        assert all(
            f"P2_FAKE_TOKEN_{other}" not in request.url and f"P2_FAKE_COOKIE_{other}" not in str(request.headers)
            for request in adapter.requests
        )
    assert (core.session, core._em_validate_key, core.ocr) == old_state


@pytest.mark.parametrize("stage", ["login", "post", "json"])
def test_failed_operation_releases_lock_without_corrupting_another_instance(client_factory, stage):
    client = ready(client_factory())
    other = ready(client_factory(), "P2_FAKE_OTHER_TOKEN")
    other._session.cookies.set("other", "P2_FAKE_OTHER_COOKIE")
    other._session.post.return_value = response(["P2_FAKE_OTHER_RESULT"])
    error = ValueError("P2_FAKE_ERROR")
    if stage == "login":
        client._session.get.side_effect = error
    elif stage == "post":
        client._session.post.side_effect = error
    else:
        reply = response({})
        reply.json = lambda: (_ for _ in ()).throw(error)
        client._session.post.return_value = reply
    with pytest.raises(ValueError, match="P2_FAKE_ERROR") as caught:
        (client.login if stage == "login" else client.query_orders)()
    assert caught.value is error
    workers = Workers()
    workers.start(other.query_orders)
    assert workers.finish() == [["P2_FAKE_OTHER_RESULT"]]
    expected = "P2_FAKE_OTHER_TOKEN"
    assert other._token == expected
    assert other._session.cookies.get("other") == "P2_FAKE_OTHER_COOKIE"
