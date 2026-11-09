============
Installation
============

Support target for 0.3.0: CPython 3.11 on Linux only
(``>=3.11,<3.12``). Other Python versions, macOS, Windows and PyPy are not
verified. ddddocr 1.4.11 requires Python <3.12 and is not upgraded without
an approved OCR image regression set.

At the command line (currently installs the historical public stable release,
not the unpublished 0.3.0 candidate)::

    pip install emtl

After a separately authorized Beta upload only::

    python -m pip install --pre emtl==0.3.0b1

Do not treat Beta as production stability or broker-protocol assurance. Import,
CLI help and synthetic offline tests suffice for automated installation checks;
never put real credentials or live trades into CI. See :doc:`releasing` for
upgrade, rollback limitations and feedback requirements.
