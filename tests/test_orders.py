from unittest.mock import Mock
from unittest.mock import PropertyMock

import pytest
import requests

from emtl import core
from emtl.const import _urls
from tests.helpers import protocol_cases
from tests.helpers import response


@pytest.mark.parametrize("trade_type", ["B", "S"])
@pytest.mark.parametrize("status", [0, -1])
def test_order_form_and_business_response(monkeypatch, trade_type, status):
    cases = protocol_cases()
    value = cases["order_response"] if status == 0 else cases["order_rejected"]
    session = Mock(post=Mock(return_value=response(value)))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    assert core.create_order(" FAKE ", trade_type, "SA", 1.25, 100) == value
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["create_order"] + "P1_FAKE_TOKEN",)
    assert session.post.call_args.kwargs["data"] == {
        "stockCode": " FAKE ",
        "tradeType": trade_type,
        "zqmc": "",
        "market": "SA",
        "price": 1.25,
        "amount": 100,
    }
    assert session.post.call_args.kwargs["headers"]["X-Requested-With"] == "XMLHttpRequest"


@pytest.mark.parametrize("operation", ["create", "cancel"])
@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError, requests.exceptions.ChunkedEncodingError])
def test_uncertain_submission_is_never_retried(monkeypatch, operation, error_type):
    events = []
    error = error_type("P1_FAKE_RESPONSE_LOST")

    def post(*args, **kwargs):
        events.append("P1_FAKE_SUBMITTED")
        raise error

    session = Mock(post=Mock(side_effect=post))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    call = (
        (lambda: core.create_order("FAKE", "B", "SA", 1.0, 100))
        if operation == "create"
        else (lambda: core.cancel_order(" P1_FAKE_ORDER "))
    )
    with pytest.raises(error_type) as caught:
        call()
    assert caught.value is error
    assert events == ["P1_FAKE_SUBMITTED"]
    session.post.assert_called_once()


@pytest.mark.parametrize("operation", ["create", "cancel"])
@pytest.mark.parametrize(("reply", "exception"), [(None, AttributeError), (response(text="failed", status=500), RuntimeError)])
def test_bad_http_response_is_not_retried(monkeypatch, operation, reply, exception):
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    call = (
        (lambda: core.create_order("FAKE", "B", "SA", 1.0, 100))
        if operation == "create"
        else (lambda: core.cancel_order(" P1_FAKE_ORDER "))
    )
    with pytest.raises(exception):
        call()
    session.post.assert_called_once()


@pytest.mark.parametrize("failure_index", [1, 2])
def test_order_json_failure_is_not_retried(monkeypatch, failure_index):
    error = ValueError("P1_FAKE_BODY")
    reply = response({})
    reply.json = Mock(side_effect=[error] if failure_index == 1 else [{}, error])
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    with pytest.raises(ValueError, match="P1_FAKE_BODY") as caught:
        core.create_order("FAKE", "S", "SA", 1.0, 100)
    assert caught.value is error
    assert reply.json.call_count == failure_index
    session.post.assert_called_once()


@pytest.mark.parametrize(("order", "text", "expected"), [("  ", "  ", ""), (" P1_FAKE ", " rejected \n", "rejected")])
def test_cancel_preserves_text_response(monkeypatch, order, text, expected):
    session = Mock(post=Mock(return_value=response(text=text)))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    assert core.cancel_order(order) == expected
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["cancel_order"] + "P1_FAKE_TOKEN",)
    assert session.post.call_args.kwargs["data"] == {"revokes": order.strip()}


def test_cancel_text_failure_propagates_without_retry(monkeypatch):
    error = requests.exceptions.ChunkedEncodingError("P1_FAKE_TEXT_LOST")
    reply = response(text="unused")
    text = PropertyMock(side_effect=error)
    monkeypatch.setattr(type(reply), "text", text)
    session = Mock(post=Mock(return_value=reply))
    monkeypatch.setattr(core, "session", session)
    monkeypatch.setattr(core, "_em_validate_key", "P1_FAKE_TOKEN")
    with pytest.raises(requests.exceptions.ChunkedEncodingError) as caught:
        core.cancel_order(" P1_FAKE_ORDER ")
    assert caught.value is error
    session.post.assert_called_once()
    assert session.post.call_args.args == (_urls["cancel_order"] + "P1_FAKE_TOKEN",)
    assert session.post.call_args.kwargs["data"] == {"revokes": "P1_FAKE_ORDER"}
    text.assert_called_once_with()
