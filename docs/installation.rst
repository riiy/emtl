========
安装说明
========

版本与支持范围
==============

OCR v1 源码开发分支支持 Linux / CPython 3.11、3.12、3.13
（``>=3.11,<3.14``），Windows、macOS 和 PyPy 尚未验证。
开发分支默认安装 Pillow 13.0.0 与冻结的微型 CNN 模型，
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
本段描述未合并的 OCR v1 开发分支；已发行版本的依赖可能不同。

安装已公开的版本
================

以下命令安装 PyPI 上已有的公开稳定版本，**不会** 安装尚未获准上传的
``0.3.0b1`` Beta 候选（内部 Alpha ``0.3.0a1`` 亦未对外发布）::

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
