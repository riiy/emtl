# Context contains only artifacts/, wheelhouse/ (possibly empty) and the two
# smoke scripts. Dependency preparation is not a test and may use the network.
FROM python:3.11-bookworm
WORKDIR /smoke
COPY artifacts/ /artifacts/
COPY wheelhouse/ /wheelhouse/
COPY package_smoke.py check_offline_network.py ./
ARG PIP_NO_INDEX=0
RUN python -m venv /venvs/wheel && python -m venv /venvs/sdist && \
    /venvs/wheel/bin/pip install --find-links=/wheelhouse /artifacts/*.whl && \
    /venvs/sdist/bin/pip install --find-links=/wheelhouse /artifacts/*.tar.gz
ENV PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# Execute this image with --network none; the first command independently checks it.
CMD ["sh", "-ec", "python check_offline_network.py; /venvs/wheel/bin/python package_smoke.py \"$EXPECTED_VERSION\"; /venvs/sdist/bin/python package_smoke.py \"$EXPECTED_VERSION\""]
