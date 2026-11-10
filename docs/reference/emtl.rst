emtl
====

The 0.3.0 support target is CPython 3.11 on Linux. Public signatures, successful
return values and CLI arguments/exit codes remain subject to the contracts below.
Additions require contract tests; deprecations require release notes and migration
instructions. Removals or other breaking changes need separate maintainer approval
and a version decision; no removal is authorized by P4.

The legacy API and compatibility baseline are documented in the
:download:`P0 public API contract <../refactor/contracts/P0-public-api.md>`.

The synchronous account-bound client is documented in the
:download:`P2 client API contract <../refactor/contracts/P2-client-api.md>`.

Trade uncertainty and safe HTTP errors for the explicit client are documented in
the :download:`P3 trade error contract <../refactor/contracts/P3-trade-errors.md>`.

Current exported API
--------------------

``emtl.__all__`` exports the nine legacy module-level functions plus
``TradingClient``. The legacy functions retain their original identities
and use shared state in ``emtl.core``; see the P0 contract above.

The synchronous, account-bound ``TradingClient`` provides:

* ``login(duration=30)`` and ``close()``;
* ``query_asset_and_position()``, ``query_orders()``, ``query_trades()``;
* ``query_history_orders(size, start_time, end_time)``,
  ``query_history_trades(size, start_time, end_time)``,
  ``query_funds_flow(size, start_time, end_time)``;
* ``get_last_price(symbol_code, market)``;
* ``create_order(stock_code, trade_type, market, price, amount)`` and
  ``cancel_order(order_str)``.

``TradeOutcomeUnknown`` and ``BrokerHTTPError`` are imported from
``emtl.errors`` and are not exported in the package-level ``__all__``.
They apply to the explicit client under the P3 contract, not the legacy
module-level calls. See :doc:`../usage` for manual usage and safety notes.

.. testsetup::

    from emtl import *

.. automodule:: emtl
    :members:
    :undoc-members:
    :special-members: __init__, __len__
