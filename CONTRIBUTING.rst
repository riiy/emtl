========
参与贡献
========

欢迎提交缺陷修复、文档改进与经过验证的新功能。
本项目由维护者决定发布范围和发布时机。

报告问题
========

请通过 `GitHub Issues <https://github.com/riiy/emtl/issues>`_ 反馈一般问题，
并尽量包含：

- 操作系统及版本、Python 与 emtl 版本、安装方式。
- 复现步骤、预期结果与实际结果。
- **只使用合成数据** 的最小复现样例。

不要公开密码、验证码图片或文本、token、Cookie、账户标识、
完整 HTTP 请求/响应或真实交易记录。
安全漏洞、重复下单和账户混用风险请依照 ``SECURITY.md`` 私密报告，
不要在公开 Issue 或 PR 中上传敏感内容。

改进文档和提出需求
==================

欢迎修改 RST 文档、公开接口文档及代码注释。
目前官方文档以**简体中文单语**维护，技术标识、API 名称和命令保持原样。
提交需求时请明确用途、预期行为、兼容影响及最小实现范围；
不默认接受额外架构改造或新的生产交易能力。

开发与测试
==========

请使用 Python 3.11。测试必须使用合成账户并在系统级网络隔离下运行，
禁止让旧真实交易测试重新进入 CI，也不要把真实凭证写入测试或构建产物。

从仓库根目录使用 ``python -m pytest`` 或 ``tox -e py311-cover``
运行测试，并启用现有的网络隔离保护。``tox -e docs`` 仅构建 HTML；
联网的 ``tox -e linkcheck`` 需单独运行，不能当成离线测试。

测试代码位于 checkout 下的 ``tests/``，不随安装包分发；
从其他目录运行时须显式传入 checkout 中 ``tests/`` 的绝对路径，
不再使用 ``pytest --pyargs emtl``。

独立的 ``Offline tests (network namespace)`` CI 工作流会先准备依赖，
随后在 Docker ``NetworkMode=none`` 容器中执行测试，
并上传 tox、coverage 和隔离证据。
本地复现时使用 ``ci/offline.Dockerfile`` 构建镜像，
运行容器时传入 ``--network none``，并核对容器退出码和网络模式。

贡献流程
========

1. 在 GitHub `Fork 仓库 <https://github.com/riiy/emtl>`_ 并克隆::

       git clone git@github.com:YOURGITHUBNAME/emtl.git

2. 创建工作分支::

       git checkout -b name-of-your-fix

3. 在隔离环境完成修改和适用的测试、文档检查::

       tox

4. 经维护者批准后提交并推送自己的分支::

       git add .
       git commit -m "Describe the change"
       git push origin name-of-your-fix

5. 提交 Pull Request，记录改动目的、验证证据与剩余风险。

PR 审核应检查测试结果、API/兼容性文档、``CHANGELOG.rst``
及必要的 ``AUTHORS.rst`` 更新；不要因 CI 通过自动宣布可发布。
创建 Tag、GitHub Release 或上传 PyPI 均需单独授权。

常用命令
========

运行部分测试（环境名与筛选条件按实际配置调整）::

    tox -e py311-cover -- pytest -k test_myfeature

并行运行适用的 tox 环境::

    tox -p auto
