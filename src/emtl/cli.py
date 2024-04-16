"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -memtl` python will execute
    ``__main__.py`` as a script. That means there will not be any
    ``emtl.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there"s no ``emtl.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse

from .core import emt

parser = argparse.ArgumentParser(prog="emt", description="东方财富交易系统", epilog="东方财富交易系统")
parser.add_argument("-u", "--user", required=True)
parser.add_argument("-p", "--password", required=True)


def run(args=None):
    args = parser.parse_args(args=args)
    print(emt(args.user, args.password))
    parser.exit(0)
