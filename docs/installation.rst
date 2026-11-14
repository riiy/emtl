========
安装说明
========

版本与支持范围
==============

``0.3.0`` Stable 使用已发布 ``0.3.0b2`` 的功能基线，
CPython 支持范围仍为 3.11、3.12、3.13
（``Requires-Python >=3.11,<3.14``）。维护者在 Ubuntu x86_64
和 macOS Intel x86_64 的三个 Python 版本上，分别从 PyPI 安装
Beta ``0.3.0b2`` 并完成 10 次真实账户登录，六组合计 60/60。
这些实测不能证明 ``0.3.0`` Stable 的交易功能、长期稳定性或
未经验证的其他 Linux/macOS 架构；Apple Silicon、Windows、PyPy
未验证。详见
:download:`Beta 实测验收报告 <refactor/reports/v0.3.0b2-beta-field-acceptance.md>`。
Stable 的发布决策及例外见
:download:`Stable 发布决策 <refactor/reports/v0.3.0-stable-release-decision.md>`。

Stable ``0.3.0`` 与 Beta ``0.3.0b2`` 默认安装 Pillow 13.0.0 与冻结的微型 CNN 模型，
不再强制安装 ddddOCR、NumPy、ONNX Runtime 或 OpenCV。

在 Python 3.11 上需要旧 OCR 时，可以安装额外依赖::

    python -m pip install 'emtl[ddddocr]'

并显式选择引擎::

    export EMTL_OCR_ENGINE=ddddocr

未设置 ``EMTL_OCR_ENGINE`` 时默认使用 ``lightweight``。
未安装的旧引擎或未知引擎会明确失败，不进行静默回退。
OCR 的返回值为四位数字字符串，前导零会原样提交。

**体积限制仅适用于目标部署环境。** 目标机器源码构建 Pillow 后，
已测量 Pillow + 推理代码 + 模型约 5.72 MB，P95 约 55.76 ms；
官方 Pillow Wheel 安装可以超过 20 MB，不构成普通用户安装失败。
源码构建依赖系统 JPEG/zlib 库，必须在目标环境自行验证。
OCR v1 已随 ``0.3.0b2`` 发布；此前的 ``0.3.0b1``
仍使用旧版 ddddOCR。

安装 Stable 版本
===============

``0.3.0`` 正式完成 PyPI 上传后，使用固定版本安装::

    python -m pip install emtl==0.3.0

不指定版本时，pip 选择 PyPI 上符合当前环境的可用稳定版本，
不会默认安装 Beta 等预发布版本::

    python -m pip install emtl

**仅仅合并 Stable 候选或创建 Tag，不等于 ``0.3.0`` 已在 PyPI 发布。**
应先查看 https://pypi.org/project/emtl/ 的实际发行记录。
开发中的源码可以从 GitHub 获取，但不代表已完成正式发布验收::

    python -m pip install https://github.com/riiy/emtl/archive/master.zip

预发布版本
==========

此前的 Beta ``0.3.0b1`` 可通过显式版本号安装（仍采用旧 OCR，
仅支持 Python 3.11）::

    python -m pip install --pre emtl==0.3.0b1

``0.3.0b2`` 已在 PyPI 公开发布，使用默认的轻量 OCR 引擎。
在明确接受 Beta 和非官方接口风险后，可显式安装::

    python -m pip install --pre emtl==0.3.0b2

Beta 与 Stable 均不代表已验证生产实盘交易安全，也不保证券商协议兼容。
自动安装验收仅允许 import、CLI help、离线合成用例等无交易副作用的检查。
不要在 CI 中使用真实凭证或真实下单/撤单。
维护者的真实账户登录实测不属于自动化 CI 验收。

升级风险、版本回退限制和反馈要求参见 :doc:`releasing`。
