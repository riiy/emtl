========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |github-actions| |codecov|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations| |commits-since|
.. |docs| image:: https://readthedocs.org/projects/emtl/badge/?style=flat
    :target: https://readthedocs.org/projects/emtl/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/riiy/emtl/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/riiy/emtl/actions

.. |codecov| image:: https://codecov.io/gh/riiy/emtl/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://app.codecov.io/github/riiy/emtl

.. |version| image:: https://img.shields.io/pypi/v/emtl.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/emtl

.. |wheel| image:: https://img.shields.io/pypi/wheel/emtl.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/emtl

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/emtl.svg
    :alt: Supported versions
    :target: https://pypi.org/project/emtl

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/emtl.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/emtl

.. |commits-since| image:: https://img.shields.io/github/commits-since/riiy/emtl/v0.2.6.svg
    :alt: Commits since latest release
    :target: https://github.com/riiy/emtl/compare/v0.2.6...master



.. end-badges

东方财富自动交易接口

* Free software: MIT license

Installation
============

The next release targets **CPython 3.11 on Linux only**
(``Requires-Python >=3.11,<3.12``). Windows, macOS, PyPy and Python 3.12+
are not verified support targets. ddddocr remains at 1.4.11; upgrading OCR
requires a separately approved non-sensitive image regression set.

The current work is an unpublished internal ``0.3.0a1`` candidate for
``0.3.0``. The command below installs the existing public stable version,
not this candidate. Beta ``0.3.0b1`` will require separate upload approval.

::

    pip install emtl

You can also install the in-development version with::

    pip install https://github.com/riiy/emtl/archive/master.zip


Python interfaces
=================

The library provides two Python APIs with different safety boundaries:

* Legacy module-level functions such as ``emtl.login()`` and
  ``emtl.create_order()`` share process-level Session and token state;
  they are preserved for compatibility, not account isolation.
* ``emtl.TradingClient`` is a synchronous, account-bound client with its
  own Session, cookies and token. Use ``close()`` in a ``finally`` block;
  it has no ``with`` or asynchronous API.

An attempted trade POST with an unconfirmed outcome on ``TradingClient``
raises ``emtl.errors.TradeOutcomeUnknown``. Never automatically resubmit.
Legacy module-level functions do not provide this new error contract.
Offline tests do not establish real broker acceptance or execution.

The ``emt`` command and ``python -m emtl`` currently parse options only:
they do not log in, query the account, or submit trades. See the
`usage guide <https://emtl.readthedocs.io/en/latest/usage.html>`_.

Documentation
=============


https://emtl.readthedocs.io/

Read the Docs is the only canonical documentation site. GitHub Pages is a
mirror, not a second source of release or support guarantees.

Release and maintenance procedures: https://emtl.readthedocs.io/en/latest/releasing.html


Development
===========

Use CPython 3.11. Tests use synthetic accounts and must run without network
access; they do not establish real broker protocol or execution correctness.
No automatic retry, resubmission or trade compensation is provided.

To run all the tests run::

    pip install -r ci/requirements.txt
    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox


Getting help
============


Join `Telegram group <https://t.me/em_trade_lib>`_. Asking a question here is often the quickest way to get a pointer in the right direction.
