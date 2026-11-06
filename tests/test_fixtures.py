from tests.helpers import protocol_cases


def test_synthetic_cases_have_required_types_and_order_link():
    cases = protocol_cases()
    assert isinstance(cases["asset_response"]["Data"], list)
    assert isinstance(cases["login_accepted"]["Status"], int)
    order = cases["order_response"]["Data"][0]
    assert cases["cancel_input"] == f"{order['Wtrq']}_{order['Wtbh']}"
    assert isinstance(cases["cancel_response"], str)
    assert 'id="em_validatekey"' in cases["token_html"]
    cases["asset_response"]["Data"].append("changed")
    assert protocol_cases()["asset_response"]["Data"] == []
