=====
Usage
=====

The Python API can contact the broker when executed with the default HTTP
Session. Examples in this page are for authorized manual use, not CI tests;
offline tests must use synthetic credentials and isolated HTTP/OCR doubles.

Account-bound TradingClient
---------------------------

Prefer ``emtl.TradingClient`` for distinct accounts. ``username`` must be
supplied explicitly; an omitted ``password`` is read once from ``EM_PASSWORD``
when the client is created. Each client owns its Session, cookies and token.
Operations on the same normalized account are serialized in one process;
different accounts can overlap. Call ``close()`` in ``finally``; the client
does not implement a context manager or an asynchronous API.

The following **manual-only** example authenticates and performs a read-only
query. It still makes real network requests when run with a normal Session.

.. code-block:: python

    import os

    from emtl import TradingClient

    client = TradingClient(os.environ["EM_USERNAME"])
    try:
        if client.login() is None:
            raise RuntimeError("authentication required")
        orders = client.query_orders()
    finally:
        client.close()

``login(duration=30)`` returns a nonempty token or ``None`` when the
authentication evidence is insufficient; transport and parsing failures may
raise exceptions. The first protected operation on a new client may attempt
login once. After a failed login, explicitly call ``login()`` to retry
authentication. ``get_last_price(symbol_code, market)`` does not log in.

Trading calls and unknown outcomes
----------------------------------

``TradingClient.create_order(stock_code, trade_type, market, price, amount)``
and ``TradingClient.cancel_order(order_str)`` may submit real orders or
cancellations. At most one business POST is attempted per call; the SDK
does not automatically retry an uncertain trade, reconcile or compensate it.

* ``emtl.errors.TradeOutcomeUnknown`` indicates an attempted trade POST
  boundary with unconfirmed outcome. Its ``operation``, ``reason`` and
  optional ``status_code`` describe local failure stages, not broker
  acceptance, execution, rejection or even confirmed transmission.
  **Never automatically resubmit based on this exception.**
* ``emtl.errors.BrokerHTTPError`` covers non-trading HTTP responses with
  valid integer status other than 200 for the explicit client. Other
  transport, authentication and query exceptions may propagate unchanged.

Even a normal trade return does not prove successful execution: order JSON
and cancellation text are not validated as broker business-status evidence.
See :doc:`reference/emtl` and its P2/P3 contract links for exact boundaries.

Legacy module-level API
-----------------------

``emtl.login()``, ``emtl.query_asset_and_position()``,
``emtl.query_orders()``, ``emtl.create_order()`` and
``emtl.cancel_order()`` remain available for compatibility. These
functions share a legacy module-level Session/token and do not provide
``TradingClient`` account isolation or its new safe trade exceptions.
Do not use the legacy API for concurrent account switching. Historical
signatures and behavior are documented in the P0 API contract.

Command-line interface
----------------------

``emt`` and ``python -m emtl`` currently only parse arguments and exit.
Even though ``--buy``, ``--sell`` and ``--query`` options exist,
``emtl.cli.run()`` does **not** log in, query the broker or place orders.

.. code-block:: console

    emt --help
    python -m emtl --help
