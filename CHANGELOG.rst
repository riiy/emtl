
Changelog
=========

0.3.0a1 (unreleased internal Alpha; target stable 0.3.0)
--------------------------------------------------------

* Preserve legacy package functions and CLI signatures, arguments, exit codes
  and successful response structures; CLI no longer echoes credentials (P0).
* Remove sensitive SDK logs and root logger reconfiguration; isolate tests and
  CI from real accounts using synthetic fixtures and system-level network denial.
* Add account-bound TradingClient with independent HTTP/auth state, same-account
  serialization and different-account concurrency within one process (P2).
* Add TradeOutcomeUnknown and BrokerHTTPError in emtl.errors for the explicit
  client (P3). Unknown is not evidence of execution or rejection; never resubmit
  automatically. Legacy error behavior is unchanged.
* Narrow the approved support target to CPython 3.11 / Linux,
  Requires-Python >=3.11,<3.12. Keep ddddocr 1.4.11 and existing runtime pins.
* Establish artifact installation checks and approval-gated release procedures.
  Real broker protocol and transactions are not validated by automated tests.
* Planned Beta: 0.3.0b1 on PyPI, only after separate upload approval. Stable 0.3.0
  needs a separate post-Beta decision. No release date or production assurance yet.


0.1.0 (2024-04-14)
------------------

* First release on PyPI.

0.1.1 (2024-04-16)
------------------

* Delete python3.8 python3.9 pypy.

0.1.2 (2024-04-18)
------------------

* add login && add asset position

0.1.3 (2024-04-19)
------------------

* update docs theme

0.1.5 (2024-04-24)
------------------

* update login refrence

0.1.7 (2024-04-27)
------------------

* add insert order api


0.1.8 (2024-04-30)
------------------

* delete macos actions


0.2.0 (2024-05-21)
------------------

* complete all method


0.2.1 (2024-05-29)
------------------

* add auto deploy to pypi


0.2.2 (2024-07-11)
------------------

* replace insert_order with create_order

P0 security baseline (unreleased)
---------------------------------

* Remove sensitive log output and stop configuring the host application's root logger.
* Replace live trading tests with isolated offline tests and remove CI account credential injection.
* With explicit approval, stop echoing CLI credentials; arguments and exit codes remain unchanged.
* Move offline tests outside the package to ``tests/`` and retire the unsafe ``--pyargs emtl`` test entry point.
