============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/riiy/emtl/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

emtl could always use more documentation, whether as part of the
official emtl docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/riiy/emtl/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

Tests must run offline with synthetic account data only. Never run the old
live-trading tests or put real credentials in tests or CI. Prepare Python 3.11
and the project, pytest and pytest-cov dependencies separately; from the
repository root run ``python -m pytest`` or ``tox -e py311-cover`` with the
test network guard enabled. The tox docs environment includes an online
linkcheck and is not an offline test command. Do not push or publish without
human approval. Tests live in the checkout's ``tests/`` directory, not in the
installed package. From elsewhere, pass the absolute checkout ``tests/`` path
to pytest. The old ``pytest --pyargs emtl`` entry point is no longer supported.

The separate ``Offline tests (network namespace)`` CI workflow prepares its
dependencies before running the full suite in a Docker container with external
networking disabled. Its artifacts include tox, coverage and isolation evidence.
This does not make the docs environment's online linkcheck an offline test.
For local reproduction, build ``ci/offline.Dockerfile`` and run the resulting
image with ``--network none``; inspect the network mode and container exit code.

To set up `emtl` for local development:

1. Fork `emtl <https://github.com/riiy/emtl>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone git@github.com:YOURGITHUBNAME/emtl.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes run all the checks and docs builder with one command::

    tox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``tox``).
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

Tips
----

To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel*::

    tox -p auto
