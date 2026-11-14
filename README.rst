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

.. |commits-since| image:: https://img.shields.io/github/commits-since/riiy/emtl/v0.3.0.svg
    :alt: Commits since latest release
    :target: https://github.com/riiy/emtl/compare/v0.3.0...master



.. end-badges

东方财富自动交易接口 Python 库，MIT 许可证。

**文档语言：简体中文。** API 名称、Python 代码及命令保留原始英文标识。
Read the Docs 是规范文档站点，GitHub Pages 仅为镜像。

免责声明与风险提示
==================

本项目是社区维护的 **非官方** 东方财富交易接口实现，并非东方财富或相关券商
发布、授权或背书的官方产品。项目主要面向软件技术学习、研究与交流，
不构成投资建议、收益承诺、证券经纪、投资咨询或任何形式的金融服务。
此用途说明不改变项目 ``LICENSE`` 中 MIT 许可证授予的使用权利。

- **投资和自动化交易风险**：证券价格波动可能造成本金损失。请求超时、
  网络中断、接口或认证机制变化、验证码误识别、响应解析错误、委托重复提交、
  撤单失败、订单状态未知以及第三方服务故障，都可能造成意外交易或资金损失。
  自动化测试及少量真实登录成功不代表已验证真实下单、撤单或成交。
- **非官方接口与合规**：非公开或非官方接口可能未经通知即改变、限制或停止服务。
  使用者须自行核实相关券商服务协议、账户授权、数据处理要求及适用法律法规；
  不得绕过访问控制或用于违法违规活动。
- **生产环境与责任**：本项目未获得生产实盘交易可靠性保证，不建议直接用于
  生产环境。若使用者仍选择在生产或实盘环境部署，应自行充分测试、
  设置权限和资金限制、监控及人工应急停止措施，并自行承担由使用、
  误用、策略决策或第三方服务变化引起的投资风险、运营责任和相应损失。
  在适用法律允许的最大范围内，项目作者和维护者不对因此产生的直接、
  间接或连带损失承担责任；依法不得排除或限制的责任不受本声明影响。
- **凭证及隐私安全**：使用者负责妥善保管密码、验证码、Cookie、Token
  和账户数据。不得在 Issue、日志、CI 或公开讨论中披露敏感信息；
  安全问题应按 ``SECURITY.md`` 私下报告。
- **不提供担保**：软件按 ``LICENSE`` 所载 MIT 许可证以“现状”（AS IS）
  提供，不保证正确性、持续可用性、特定用途适用性、交易执行结果或收益。
  使用前应自行评估全部风险，且本声明不取代适用法律及券商协议。

安装与支持范围
==============

``0.3.0`` Stable 沿用已发布的 ``0.3.0b2`` 的功能基线，
不增加交易或 OCR 功能，支持 CPython 3.11、3.12、3.13
（``Requires-Python >=3.11,<3.14``）。
维护者曾在 Ubuntu x86_64、macOS Intel x86_64 六组 Python 环境中，
从 PyPI 安装 Beta ``0.3.0b2`` 并分别完成 10 次真实账户登录，
共 60/60 次成功。该结果不是 ``0.3.0`` Stable 的独立实盘验证，
更不证明所有 Linux/macOS 平台或真实交易获得生产保障；
Apple Silicon、Windows、PyPy 尚未验证。

默认 OCR 为冻结微型 CNN（Pillow + Python 标准库），不会默认安装
ddddOCR、NumPy、ONNX Runtime 或 OpenCV。仅在 Python 3.11
可选安装 ``emtl[ddddocr]`` 并设置 ``EMTL_OCR_ENGINE=ddddocr``；
显式选择失败不会静默回退。OCR v1 从 ``0.3.0b2`` 开始提供；
旧版 ``0.3.0b1`` 使用原 OCR。证据见
``docs/refactor/reports/OCR-v1-acceptance.md`` 和
``docs/refactor/reports/v0.3.0b2-beta-field-acceptance.md``。

已发布的 Beta：``0.3.0b1``（2026-11-10）、
``0.3.0b2``（2026-11-14）。维护者于 2026-11-14 批准
不等待建议观察期而准备 Stable 候选。源码标记为 Stable 不等于 PyPI 已上架 ``0.3.0``；应以 PyPI 上的实际发行记录为准。

在 ``0.3.0`` 正式上传 PyPI 后，可安装固定版本::

    python -m pip install emtl==0.3.0

不指定版本时，pip 从 PyPI 选择符合环境约束的可用稳定版本::

    python -m pip install emtl

仍可显式安装此前的 OCR Beta 进行比较::

    python -m pip install --pre emtl==0.3.0b2

如需获取开发中的源码，可从仓库安装，但源码不等于已验证的正式发布版本::

    python -m pip install https://github.com/riiy/emtl/archive/master.zip

Stable 是正式发行渠道，**不意味着真实下单、撤单、成交或长期运行安全性已得到验证**。
本项目仍是非官方接口，生产与投资风险免责声明继续适用。
正式版发布与安装验收归档：
``docs/refactor/reports/v0.3.0-stable-release-acceptance.md``。

Python 接口
===========

emtl 提供两套兼容边界不同的接口：

- **旧模块级函数**：如 ``emtl.login()`` 和 ``emtl.create_order()``。
  这些函数复用进程级 Session 和认证令牌，保留历史行为，**不保证多账户隔离**。
- **``emtl.TradingClient``**：同步、显式绑定账户的客户端，独立管理
  Session、Cookie 和 token。使用完毕须在 ``finally`` 中调用 ``close()``；
  当前不支持 ``with`` 或异步接口。

对于 ``TradingClient``，交易 POST 开始尝试后若结果无法确定，
将抛出 ``emtl.errors.TradeOutcomeUnknown``。 **不得据此自动重发订单**。
旧模块级函数不具备这项新异常契约。离线测试也不能证明真实券商已受理或成交。

命令行 ``emt`` 与 ``python -m emtl`` 当前只负责解析参数，
**不会** 实际登录、查询或提交交易。

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

开发及 CI 覆盖 CPython 3.11、3.12、3.13。自动测试只使用合成账户和禁网环境，
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
