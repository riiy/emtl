"""Wrapper return contracts, separate from HTTP/no-resubmission evidence."""

from unittest.mock import Mock

import pytest
from requests import Response

from emtl import core
from tests.helpers import QUERY_CALLS
from tests.helpers import response

WRAPPERS = [
    *QUERY_CALLS,
    ("create_order", ("P1_FAKE", "B", "SA", 1.0, 100)),
    ("cancel_order", (" P1_FAKE_ORDER ",)),
]


@pytest.mark.parametrize(("name", "args"), WRAPPERS)
def test_wrapper_seam_none_returns_none_once(monkeypatch, name, args):
    # None cannot naturally leave today's _query_something: HTTP None fails
    # _check_resp first. Only replace this dependency of the *wrapper* under
    # test, as permitted by P1 §5.1; never count this as HTTP retry evidence.
    query_dependency = Mock(return_value=None)
    monkeypatch.setattr(core, "_query_something", query_dependency)
    assert getattr(core, name)(*args) is None
    query_dependency.assert_called_once()


@pytest.mark.parametrize(("name", "args"), WRAPPERS)
def test_false_response_traverses_request_chain_once(monkeypatch, name, args):
    class FalseResponse(Response):
        def __bool__(self):
            return False

    # Synthetic status=200/false response reaches the otherwise inaccessible
    # wrapper branch while still executing _query_something and _check_resp.
    reply = FalseResponse()
    reply.status_code = 200
    reply.json = Mock(side_effect=AssertionError("false response must not be parsed"))
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    assert getattr(core, name)(*args) is None
    session.post.assert_called_once()
    reply.json.assert_not_called()


@pytest.mark.parametrize(("name", "args"), WRAPPERS[:-1])
def test_json_result_identity_is_preserved(monkeypatch, name, args):
    value = ["P1_FAKE_OPAQUE_RESULT"]
    reply = response(value)
    reply.json = Mock(side_effect=[{"first": "ignored"}, value] if name == "create_order" else [value])
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    assert getattr(core, name)(*args) is value
    session.post.assert_called_once()
    assert reply.json.call_count == (2 if name == "create_order" else 1)
