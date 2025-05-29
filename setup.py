#!/usr/bin/env python
import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with Path(__file__).parent.joinpath(*names).open(encoding=kwargs.get("encoding", "utf8")) as fh:
        return fh.read()


setup(
    name="emtl",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "write_to": "src/emtl/_version.py",
        "fallback_version": "0.2.6",
    },
    license="MIT",
    description="东方财富自动交易接口",
    long_description="{}\n{}".format(
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub("", read("README.rst")),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    author="Riiy",
    author_email="riiyzhou@gmail.com",
    url="https://github.com/riiy/emtl",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[path.stem for path in Path("src").glob("*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        # "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        # "Programming Language :: Python :: 3.8",
        # "Programming Language :: Python :: 3.9",
        # "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        # "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        # "Programming Language :: Python :: Implementation :: PyPy",
        # uncomment if you test on these interpreters:
        # "Programming Language :: Python :: Implementation :: IronPython",
        # "Programming Language :: Python :: Implementation :: Jython",
        # "Programming Language :: Python :: Implementation :: Stackless",
        "Topic :: Utilities",
    ],
    project_urls={
        "Documentation": "https://emtl.readthedocs.io/",
        "Changelog": "https://emtl.readthedocs.io/en/latest/changelog.html",
        "Issue Tracker": "https://github.com/riiy/emtl/issues",
    },
    keywords=[
        "autotrade",
        "trade",
        "东方财富",
        "股票",
        "交易",
        "交易机器人",
    ],
    python_requires=">=3.10",
    install_requires=["rsa==4.9", "requests==2.31.0", "ddddocr==1.4.11", "cryptography==42.0.5"],
    extras_require={
        # eg:
        #   "rst": ["docutils>=0.11"],
        #   ":python_version=='3.8'": ["backports.zoneinfo"],
    },
    setup_requires=[
        "setuptools_scm>=3.3.1",
    ],
    entry_points={
        "console_scripts": [
            "emt = emtl.cli:run",
        ]
    },
)
