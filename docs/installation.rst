========
安装说明
========

版本与支持范围
==============

计划中的 ``0.3.0`` 版本仅以 **Linux / CPython 3.11** 为验证和支持目标，
Python 版本约束为 ``>=3.11,<3.12``。Windows、macOS、PyPy 和
Python 3.12 及以上尚未验证。

当前 OCR 依赖 ``ddddocr==1.4.11``，其要求 Python 低于 3.12。
在获得合适的脱敏图片回归样本并完成验证之前，不升级 OCR 引擎。

安装已公开的版本
================

以下命令安装 PyPI 上已有的公开版本，**不会** 安装尚未发布的
``0.3.0a1`` 内部候选版本::

    python -m pip install emtl

开发中的源码可以从 GitHub 获取，但不代表已完成正式发布验收::

    python -m pip install https://github.com/riiy/emtl/archive/master.zip

预发布版本
==========

只有维护者单独批准并完成 ``0.3.0b1`` 上传后，下面的命令才有意义::

    python -m pip install --pre emtl==0.3.0b1

Beta 不代表可在生产环境安全交易，也不保证券商协议兼容。
自动安装验收仅允许 import、CLI help、离线合成用例等无交易副作用的检查。
不要在 CI 中使用真实凭证或真实下单/撤单。

升级风险、版本回退限制和反馈要求参见 :doc:`releasing`。
