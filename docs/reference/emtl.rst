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

.. testsetup::

    from emtl import *

.. automodule:: emtl
    :members:
    :undoc-members:
    :special-members: __init__, __len__
