"""Purely synthetic transports and deterministic thread coordination."""

from queue import Queue
from threading import Event
from threading import Thread
from types import MethodType
from unittest.mock import Mock

import requests
from requests.adapters import BaseAdapter

from tests.helpers import response

import conftest as bootstrap

WAIT = 5
SYNTHETIC = "P2_FAKE_TOKEN"


def fake_session():
    return Mock(cookies=requests.cookies.RequestsCookieJar(), headers={})


def ready(client, token=SYNTHETIC):
    client._token = token
    client._state = "READY"
    return client


class Workers:
    def __init__(self):
        self.threads = []
        self.results = Queue()

    def start(self, fn):
        def invoke():
            try:
                self.results.put((True, fn()))
            except BaseException as error:
                self.results.put((False, error))

        thread = Thread(target=invoke, daemon=True)
        self.threads.append(thread)
        thread.start()

    def finish(self):
        for thread in self.threads:
            thread.join(WAIT)
        assert not any(thread.is_alive() for thread in self.threads), "worker did not finish"
        values = []
        for _ in self.threads:
            success, value = self.results.get_nowait()
            if not success:
                raise value
            values.append(value)
        return values


class ObservedLock:
    """Observe real contention without adding or replacing mutual exclusion."""

    def __init__(self, lock):
        self.lock = lock
        self.contended = Event()

    def __enter__(self):
        if not self.lock.acquire(blocking=False):
            self.contended.set()
            self.lock.acquire()
        return self

    def __exit__(self, *args):
        self.lock.release()


class MemoryAdapter(BaseAdapter):
    def __init__(self, handler):
        self.handler = handler
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append(request)
        reply = self.handler(request)
        reply.request = request
        reply.url = request.url
        reply._content_consumed = True
        return reply

    def close(self):
        pass


def memory_session(handler):
    """Restore only instance request/send, with every HTTP adapter in memory.

    The global P1 guards remain installed. Both class methods are guarded, so
    recovering send alone would not exercise real PreparedRequest generation.
    No adapter here can call requests' HTTPAdapter or any socket transport.
    """
    session = requests.Session()
    session.trust_env = False
    adapter = MemoryAdapter(handler)
    for existing in session.adapters.values():
        existing.close()
    session.adapters.clear()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    originals = bootstrap._offline["install"].__globals__["_originals"]
    for owner, name, original in originals:
        if owner is requests.sessions.Session and name in {"request", "send"}:
            setattr(session, name, MethodType(original, session))
    return session, adapter


def token_reply(token=SYNTHETIC):
    return response(text=f'id="em_validatekey" type="hidden" value="{token}"')
