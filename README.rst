========
项目简介
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - 文档
      - |docs|
    * - 测试
      - |github-actions| |codecov|
    * - 发布包
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

东方财富自动交易接口 Python 库，MIT 许可证。

**文档语言：简体中文。** API 名称、Python 代码及命令保留原始英文标识。
Read the Docs 是规范文档站点，GitHub Pages 仅为镜像。

安装与支持范围
==============

计划中的下一个正式版本 ``0.3.0`` 仅以 **Linux / CPython 3.11**
为验证和支持目标（``Requires-Python >=3.11,<3.12``）。
Windows、macOS、PyPy 及 Python 3.12+ 尚未验证。
当前固定 ``ddddocr==1.4.11``；升级 OCR 需要另行批准的脱敏图像回归测试。

目前 ``0.3.0a1`` 仍是**未公开发布**的内部 Alpha 候选版本；
计划中的 PyPI Beta ``0.3.0b1`` 和正式版 ``0.3.0``
都需要维护者单独批准。以下命令安装现有公开版本，而不是内部候选版::

    python -m pip install emtl

如需获取开发中的源码，可从仓库安装，但源码不等于已验证的正式发布版本::

    python -m pip install https://github.com/riiy/emtl/archive/master.zip

Python 接口
===========

emtl 提供两套兼容边界不同的接口：

- **旧模块级函数**：如 ``emtl.login()`` 和 ``emtl.create_order()``。
  这些函数复用进程级 Session 和认证令牌，保留历史行为，**不保证多账户隔离**。
- **``emtl.TradingClient``**：同步、显式绑定账户的客户端，独立管理
  Session、Cookie 和 token。使用完毕须在 ``finally`` 中调用 ``close()``；
  当前不支持 ``with`` 或异步接口。

对于 ``TradingClient``，交易 POST 开始尝试后若结果无法确定，
将抛出 ``emtl.errors.TradeOutcomeUnknown``。**不得据此自动重发订单**。
旧模块级函数不具备这项新异常契约。离线测试也不能证明真实券商已受理或成交。

命令行 ``emt`` 与 ``python -m emtl`` 当前只负责解析参数，
**不会**实际登录、查询或提交交易。

文档
====

- `在线文档 <https://emtl.readthedocs.io/>`_
- `安装说明 <https://emtl.readthedocs.io/page/installation.html>`_
- `使用指南 <https://emtl.readthedocs.io/page/usage.html>`_
- `API 参考 <https://emtl.readthedocs.io/page/reference/emtl.html>`_
- `发布与维护 <https://emtl.readthedocs.io/page/releasing.html>`_

以上页面由 Read the Docs 提供，GitHub Pages 只是镜像。
站点由原英文项目切换为中文时，需要同步调整 Read the Docs 项目的语言设置；
本仓库不会自动修改该远端设置。

开发与测试
==========

开发使用 CPython 3.11。自动测试只使用合成账户和禁网环境，
不连接真实券商，也不验证真实下单、撤单或成交结果。
SDK 不自动重试、重发或补偿订单。

在隔离测试环境中运行（完整离线验证需额外配置系统级禁网）::

    python -m pip install -r ci/requirements.txt
    tox

``tox -e docs`` 生成 HTML；在线外链检查 ``tox -e linkcheck``
独立执行，不属于离线测试。

问题反馈
========

- `GitHub Issues <https://github.com/riiy/emtl/issues>`_
- `Telegram 讨论组 <https://t.me/em_trade_lib>`_

请勿在公开讨论中提交密码、验证码、Cookie、令牌、账户标识或交易记录。
安全与交易风险报告请遵循 ``SECURITY.md`` 的私密联系说明。
