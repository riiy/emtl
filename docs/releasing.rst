============
发布与维护
============

当前状态与支持范围
==================

内部 Alpha ``0.3.0a1`` 未对外发布；``0.3.0b1`` 已于 2026-11-10
发布为 Beta。OCR v1 已合并至 ``master``，下一候选为 PyPI Beta
``0.3.0b2``，**尚未获得 Tag、Release 或上传授权**。完成新 Beta 观察后
再单独评估正式版 ``0.3.0``；不同发布操作须分别获得明确批准。

已发行的 ``0.3.0b1`` 仅支持 Linux / CPython 3.11；新候选 ``0.3.0b2``
计划支持 Linux / CPython 3.11、3.12、3.13。其他平台和 PyPy 尚未验证。
自动测试采用合成数据与禁网环境，不能证明券商协议正确或真实成交。
Read the Docs 是规范文档站点，GitHub Pages 只是手动维护的镜像；
仅交付 RST + Sphinx 生成的 HTML，不生成 PDF、EPUB。

版本号与不可变 Tag
==================

遵循 PEP 440：``0.3.0a1``、``0.3.0b1``、``0.3.0b2``、``0.3.0rc1``、``0.3.0``，
Git Tag 使用前缀 ``v``，并与规范版本号严格对应。

``setuptools_scm`` 负责运行时版本；不含 Git 元数据的源码包必须保留
``PKG-INFO`` 或生成的版本文件。没有对应 Tag 的内部快照可能包含开发版本后缀，
不得以正式版本名宣传。

变更版本时同步核对 fallback、候选版本、文档、cookiecutter 和 bumpversion 配置。
使用 bumpversion 必须添加 ``--no-commit --no-tag``，并自行检查 diff。
README 的 commits-since 徽章在实际发布前始终指向最后已公开发布的 Tag。
禁止覆盖 Tag、复用 PyPI 版本，或以 ``skip-existing`` 隐藏冲突。

Alpha 与 Beta 门禁
==================

Alpha 仅供内部验证：使用干净 checkout、对应提交的 Build/check/docs、
Offline 和 Package Alpha CI、单个 sdist 与 wheel、严格元数据和文件审计、
独立干净虚拟环境安装、``pip check``、运行时与分发版本一致性、
API/CLI help 及构造烟测，并在系统级禁网下完成。
保留提交、工具版本、执行命令、SHA256、文件清单和安装证据。
不能使用真实账户凭证或调用券商。

Beta 必须在 Alpha 和独立 Review 后，由维护者**另行批准上传**。
只有该版本真实上传后，以下显式预发布安装命令才可使用::

    python -m pip install --pre emtl==0.3.0b2

Beta 说明至少包含版本、日期、Commit、产物哈希、环境、变更、
兼容范围、升级/降级风险和已知限制。建议观察十个工作日并按
安装/环境、文档、API 兼容、缺陷、安全/交易风险分类反馈。

没有有价值的反馈时，维护者应显式选择延长观察、暂停或评估正式版；
**沉默不能证明真实交易安全**。反馈模板仅包含 emtl/Python/OS 版本、
安装方法、脱敏的合成最小复现、预期/实际行为及异常类别。
不得索取密码、验证码、令牌、Cookie、账户标识、完整请求/响应或交易记录，
也不要求真实登录、下单或撤单的结果。

凭证泄漏、重复提交风险、账户混用、未经授权的 API 不兼容改动等阻断项
必须解决；延期须明确批准并披露。Stable 需 Beta 后再次批准，
选择发布通道本身不等于获得上传权限。

正式发布检查单
==============

每次发布都由维护者负责，按顺序完成：

#. 确认候选来自已合并、干净的 ``master`` 提交；
   该**精确 SHA** 上的 Build/check/docs、Offline 和 Package Alpha
   CI 均成功，不以 PR head 的成功结果代替。
#. 构建一次并审计、安装同一批产物；只发布通过 SHA256 核验的原文件。
   归档构建日志、JUnit、覆盖率、manifest 和工具版本。
#. 核对 Tag、SCM、sdist、wheel、运行时版本、Changelog 与发布说明一致。
   手动 Workflow 必须从 ``master`` 上的**精确目标 Tag 提交**触发；
   GitHub 事件 SHA 必须等于受测 checkout SHA，以避免 Trusted Publishing
   provenance 指向之后的提交。若 ``master`` 已前进，停止该次发布，
   重新准备获批准的候选，不得改写原验收证据。
#. 确认 ``pypi`` Environment 已配置有效 Required reviewers。
   OIDC 仅授予 Publish Job；PR 不得持有发布权限，禁止长期 PyPI Token。
   先从可信的 master/Workflow 提交复制校验器到候选工作区之外，
   以隔离 Python 运行。未验证前不得允许候选版本替换自己的
   ancestry/审批校验器，也不得提前安装候选代码提供的构建依赖。
#. 推送 Tag、上传 Beta、上传 Stable、创建 GitHub Release 均须单独批准；
   只推送 Tag 不会自动授权上传。
#. 经批准发布后，从 PyPI 核对文件名、SHA256 以及 provenance 对应的
   repository、workflow 和 commit；再从 PyPI 在全新环境安装指定版本，
   运行禁网且无交易副作用的 smoke test，并记录 PyPI URL、Run、
   Artifact ID、Tag 和 Commit。文档镜像失败独立修复，不重发包。

PyPI Environment 审批探针（不上传）
===================================

2026-11-10 的 `no-upload Probe Run #42780759403
<https://github.com/riiy/emtl/actions/runs/42780759403>`_
已在 ``master`` 提交
``8f654edbec6f29d4e39e5b63e6ad2d2b8ed28191`` 上成功执行。
``riiy`` 对 ``pypi`` 审批后 Job 成功。
这只证明本次无上传审批门禁有效，不证明 PyPI 上传成功，
也不构成第二名独立审核人的批准。原始证据见
``docs/refactor/reports/P4-acceptance.md``。

如修改了 ``pypi`` Environment 保护规则，使用以下**不上传**流程重验，
不要用真实 Release 或 PyPI 试探：

#. 在 ``master`` 上打开 GitHub Actions →
   PyPI Environment Approval Probe → Run workflow，
   将 ``run_probe=true``。
#. 在步骤开始执行前确认 ``approval-probe`` Job 显示等待审批。
#. 由配置的 reviewer 批准，确认 Job 成功，
   日志显示没有 checkout、OIDC、构建、PyPI Token 或上传。
#. 在 ``P4-acceptance.md`` 记录 Run URL、SHA、审批 API 返回、
   Job 日志及最终状态；仅当实际捕获时才记录等待状态及时间戳，
   不猜测缺失的时间。

Probe 的 ``permissions: {}`` 不请求额外权限；
GitHub 仍保留 ``metadata: read``。
它不申请 OIDC，不构建也不上传。若输入为 false 使 Job 跳过，
不能将其算作审批成功证据。

故障、回退和 Hotfix
===================

构建或测试失败：停止，不创建发布 Tag。
未上传的产物损坏：修正并重新生成候选，重复全部门禁。
上传状态不确定：先查询 PyPI 实际版本、文件名和哈希，
**不得盲目重复上传**。

已发布版本发现普通缺陷：停止推荐该版本，由维护者评估 yanking
及 GitHub Release 提示。
安全或交易风险：先停止受影响操作、私密调查，
发布脱敏公告并以唯一新版本 Hotfix 向前修复。

**安装旧版 SDK 不会撤回券商订单，也不能撤销资金变动。**
SDK 认证状态保存在内存中，没有 SDK 数据库迁移可回退；
真实券商侧状态无法通过软件包回滚恢复。

已发行的 ``0.3.0b1`` 包含 P0–P3 的离线验证，但仍缺少真实券商
协议与交易结果的生产验证，不能直接视为经过生产验证的安全回退基线。
旧 ``0.2.6`` 发布早于这些保护措施，也不能自动降级后继续交易。
只有在维护者明确验证并记录某个 known-good 版本后，
才考虑软件包级回退（先替换占位符）::

    python -m pip install --force-reinstall 'emtl==KNOWN_GOOD_VERSION'

在没有可信回退目标时，应暂停受影响功能并向前修复。
Hotfix 从明确的 stable/master 基线分支，增加最小失败回归测试，
完成全部 CI 与产物验收并另行批准发布。
禁止删除或覆盖不可变的 PyPI 版本。
应记录事故时间线、受影响版本、缓解措施、修复版本及后续行动。

维护责任与触发条件
==================

维护者每月审查依赖；重要安全公告出现时立即针对性评估。
Dependabot 只负责创建 PR，**不得自动合并**。
运行时依赖固定版本每次单独评估，不因告警批量升级。

``requests/urllib3`` 升级需验证请求次数、重定向和异常语义；
OCR 升级需获批准的脱敏图像样本。
所有变更都需离线测试、包安装及 HTML 构建。
应在 ``2027-04-01`` 前复核 CPython 3.11–3.13 支持与 OCR 依赖；
不将已验证的 Linux 环境结果直接推广到 Windows、macOS 或 PyPy。

依赖来源分别是 ``setup.py`` （运行时直接依赖）、
``pip freeze`` 和 ``pip inspect`` （已安装的传递依赖）、
``pyproject.toml`` （构建后端）、``ci/requirements.txt`` 与
``tox.ini`` （CI/测试）、``docs/requirements.txt`` （Sphinx）。
每个候选应记录工具及解析后的依赖版本。
固定版本或测试成功不等于没有漏洞。

OCR v1 已合并至 ``master``；``0.3.0b2`` 候选的运行时依赖为
``rsa==4.9``、``requests==2.33.1``、``Pillow==13.0.0``、
``cryptography==50.0.2``。旧引擎通过仅支持 Python 3.11 的
``emtl[ddddocr]`` 可选安装。该候选尚未获得发布授权，
已发行的 ``0.3.0b1`` 仍使用 ddddOCR。
此前识别的 Requests 与 cryptography 公告已有定向更新和最终 master
兼容测试证据，但不代表已完成全量 SBOM 或未来零漏洞保证。
Dependabot 中 ``rsa 4.9 → 4.9.1`` 待单独审查，不得自动合并。

Issue/PR 按安全、交易风险、缺陷、兼容性、安装、文档、依赖和用法分类。
安全报告遵循 ``SECURITY.md``，不得公开索取秘密。
CI 失败应阻断发布，保留原始失败证据，用合成数据复现，
并在最终 SHA 重新运行。
维护重点为当前 stable；旧版尽力支持，不承诺缺乏资源保障的 SLA。
每次发布或事故后记录耗时、失败、回退/Hotfix、用户反馈及维护成本。
Beta 只供自愿试用，不提供生产环境交易保障。

- :download:`安全与交易风险报告原文（英文） <../SECURITY.md>`
- :download:`P4 依赖审查记录 <refactor/reports/P4-dependency-review.md>`
