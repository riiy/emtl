FROM python:3.11-bookworm
WORKDIR /workspace
COPY setup.py pyproject.toml README.rst CHANGELOG.rst LICENSE tox.ini pytest.ini .coveragerc .dockerignore conftest.py ./
COPY src/ src/
COPY tests/ tests/
COPY ci/ ci/
COPY docs/ docs/
COPY .github/workflows/ .github/workflows/

ARG EMTL_TEST_VERSION=0.2.6
RUN python -m pip install 'tox>=4.67' && \
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_EMTL="${EMTL_TEST_VERSION}" \
    python -m tox -e py311-cover --notest -v

ENV PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
CMD ["python", "ci/run_offline_tests.py"]
