import datetime
import os

from emtl.core import query_funds_flow
from emtl.core import query_history_orders
from emtl.core import query_history_trades
from emtl.core import query_orders
from emtl.core import query_trades

from .. import emt
from .. import login
from .. import query_asset_and_position


def test_emt():
    assert emt("user", "pass") == ("user", "pass")


def test_emt_empty():
    assert emt("", "") == ("", "")


def test_login():
    validate_key = login(os.getenv("EM_USERNAME", ""), os.getenv("EM_PASSWORD", ""))
    assert validate_key
    assert len(validate_key) == len("b91d8012-b70b-4265-bb5d-f79442531017")


def test_query_asset_position():
    resp = query_asset_and_position()
    assert resp
    assert resp["Status"] == 0


def test_query_orders():
    resp = query_orders()
    assert resp
    assert resp["Status"] == 0


def test_query_trades():
    resp = query_trades()
    assert resp
    assert resp["Status"] == 0


def test_query_history_orders():
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(30)
    st = start_date.strftime("%Y-%m-%d")
    et = end_date.strftime("%Y-%m-%d")

    resp = query_history_orders(100, st, et)
    assert resp
    assert resp["Status"] == 0


def test_query_history_trades():
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(30)
    st = start_date.strftime("%Y-%m-%d")
    et = end_date.strftime("%Y-%m-%d")

    resp = query_history_trades(100, st, et)
    assert resp
    assert resp["Status"] == 0


def test_query_funds_flow():
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(30)
    st = start_date.strftime("%Y-%m-%d")
    et = end_date.strftime("%Y-%m-%d")

    resp = query_funds_flow(100, st, et)
    assert resp
    assert resp["Status"] == 0
