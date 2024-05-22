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

.. |commits-since| image:: https://img.shields.io/github/commits-since/riiy/emtl/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/riiy/emtl/compare/v0.2.0...master



.. end-badges

东方财富自动交易接口

* Free software: MIT license

Installation
============

::

    pip install emtl

You can also install the in-development version with::

    pip install https://github.com/riiy/emtl/archive/master.zip


Documentation
=============


https://emtl.readthedocs.io/


Development
===========

To run all the tests run::

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
