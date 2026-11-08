# P4 · 发布、兼容性与持续维护实施计划（emtl）

> **状态：实施计划草案，等待维护者审查；尚未批准 Build 或发布。**
>
> 需求：`docs/refactor/requirements/P4.md`
>
> 建议分支：`refactor/p4-release-maintenance`。
>
> 计划创建时基线：`master` HEAD `225d4e59c9689ed7414a2f0aa9d0a1c7ac8c8fbb`；P4 分支 HEAD `d891d704ff808be66f4430cce2b2dad8467a0c30`。实施前必须重新核实，不能把这些 SHA 当作未来最新版本。
>
> 本文件只定义实施顺序、决策、修改范围和验收证据。**本次没有修改生产代码、测试、CI 配置、依赖、版本、tag 或发布状态。**
>
> **安全硬约束：** P0–P3 的系统级禁网、合成账户、禁止真实凭证、禁止真实登录/查询/下单/撤单继续有效。Alpha、Beta、包安装测试和正式发布门禁都不得以真实交易作为自动验收。正式 PyPI 发布、创建正式 tag、GitHub Release 和任何真实账户验证均需另行明确授权。

## 1. 结论与推荐路径

P4 的交付重点是建立可重复、可审计的包构建和发布闭环。建议按以下顺序实施：

1. **先解决兼容性声明失真。** 当前 emtl 的 Python 声明与 ddddocr 的依赖元数据冲突；不能直接扩大 Python 支持矩阵。
2. **把 P0–P3 已完成但尚未进入 PyPI 的变更作为一次明确版本交付。** 建议下一版本为 `0.3.0`，采用 Alpha → Beta → Stable；版本号方案仍需维护者批准。
3. **保持 ddddocr 1.4.11，不在本阶段无样本升级 OCR 引擎。** 先以 Python 3.11 作为唯一已验证运行时；如果未来要支持 Python 3.12+，另行通过 OCR 兼容性 Kill Test。
4. **复用现有 GitHub Actions、Offline tests、setuptools_scm、PyPI Trusted Publishing、tox 和 Sphinx。** 只补足包产物测试、发布权限和证据关联，不引入数据库、队列、遥测或新的商业平台。
5. **发布失败优先修复前进。** PyPI 现有 0.2.6 版本早于 P0–P3，不能把它作为默认安全回滚版本。

推荐的首轮交付边界：

- Python：CPython 3.11；不宣称支持 Python 3.10、3.12+。
- OS：仅声明 Linux/CPython 为已验证环境；不新增 Windows/macOS 支持承诺。
- 版本：`0.3.0a1`（内部 Alpha）→ `0.3.0b1`（Beta）→ `0.3.0`（正式版）。
- Beta：优先使用 PyPI pre-release，用户必须显式安装；若维护者不希望公开 PyPI Beta，可改用 GitHub Pre-release。
- 文档：Read the Docs 作为默认官方文档入口，继续 HTML + RST + Sphinx，不生成 PDF/EPUB；GitHub Pages 是否保留需先确认是否仍有实际使用者。
- 发布：构建一次、测试同一批产物、发布同一批产物；PyPI OIDC 只授予独立 Publish job，并由受保护的 `pypi` environment 审批。

## 2. 已核实的仓库与外部基线

以下事实来自创建计划时的 GitHub 仓库只读检查和公开包元数据。Build 开始时仍须重新核实。

### 2.1 Git 与阶段状态

| 项目 | 已核实事实 |
| --- | --- |
| 仓库 | `riiy/emtl` |
| master HEAD | `225d4e59c9689ed7414a2f0aa9d0a1c7ac8c8fbb` |
| P4 分支 HEAD | `d891d704ff808be66f4430cce2b2dad8467a0c30` |
| P4 Requirements blob | `be5d5529263b3c2baeaee046dc8655e4aae34d7d` |
| P4 Plan | 当前不存在；本文件为首次创建 |
| P0–P3 | P3 最终验收报告 `14 记录 P3 PASS、已合并 master；最终远端 Build/Offline tests、Artifact、Tree 和独立 Review 已闭环 |
| 历史测试基线 | P3 最终远端三种入口各 467 passed；这是 P3 历史证据，不代替 P4 当前提交的重新验收 |

当前可见 Git tags 为 `v0.1.0` 至 `v0.2.6`。最新 tag `v0.2.6` 指向提交 `89328a75ea42362587fb46e6a9f395d0ca90ee86`，tagger 日期为 2025-05-29；该 tag 是 annotated tag，但 GitHub 元数据标记为 unsigned。不要假设仓库已存在 0.2.7 或 0.3.0 tag。

### 2.2 当前 PyPI 发布状态

PyPI 当前可见最新稳定版本为 `emtl 0.2.6`，发布日期 2025-05-29，包含 sdist 和纯 Python wheel；两种产物均有 PyPI provenance，来源为 GitHub Actions Trusted Publishing，构建提交为 `89328a75ea42362587fb46e6a9f395d0ca90ee86`。

公开元数据显示：

- Requires-Python：`>=3.10`。
- Python classifier：仅列出 Python 3.11。
- 操作系统 classifier：Unix、POSIX。
- 当前 master 的 P0–P3 变更还未形成新的 PyPI 稳定版本。
- `CHANGELOG.rst` 目前只有 P0 security baseline 的 unreleased 记录，没有完整呈现 P1–P3 的用户可见变更。

来源：

- [PyPI emtl 0.2.6](https://pypi.org/project/emtl/0.2.6/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [PyPI provenance / attestations](https://docs.pypi.org/attestations/)

### 2.3 包版本来源存在多处副本

当前仓库有以下版本定义：

| 文件 | 当前行为 |
| --- | --- |
| `setup.py` | setuptools_scm；`write_to="src/emtl/_version.py"`；fallback version 为 `0.2.6` |
| `src/emtl/__init__.py` | `__version__ = "0.2.6"`，静态版本字符串 |
| `docs/conf.py` | 优先读已安装 distribution metadata；失败时打印 traceback 并回退到 `0.2.6` |
| `.bumpversion.cfg` | `current_version = 0.2.6`；配置了自动 commit/tag，并同步 setup.py、README、docs/conf.py、__init__.py、cookiecutterrc |

这些值当前一致，但发布时存在版本漂移风险。特别是 .bumpversion.cfg 默认 `commit=True`、`tag=True`，不能在未经确认的情况下直接运行默认 bumpversion 命令。

P4 不要求重写整个版本体系；优先沿用 setuptools_scm 和现有 bumpversion 配置，增加严格的一致性检查，并在更新版本文件时显式禁用自动 commit/tag。

### 2.4 Python 与运行时依赖存在实际冲突

当前 `setup.py`：

- `python_requires=">=3.10"`
- `rsa==4.9`
- `requests==2.31.0`
- `ddddocr==1.4.11`
- `cryptography==42.0.5`

关键事实：

1. Python 官方版本状态页标记 Python 3.10 于 **2026-10-01 EOL**，不再获得上游安全更新。Python 3.11 仍在安全维护期，预计至 2027-10。
2. ddddocr 1.4.11 的 PyPI 元数据要求 Python `<3.12`。因此 emtl 当前 `>=3.10` 的声明并不代表 3.12+ 可安装；pip resolver 会受到依赖元数据限制。
3. ddddocr 1.6.1 于 2026-03-11 发布，元数据为 Python `>=3.10`，classifier 列出 Python 3.10–3.13；但升级 OCR 引擎可能改变验证码识别结果。
4. 当前 `tests/fixtures/` 只有合成协议 JSON，没有真实或脱敏验证码图片回归集；认证测试使用 Mock OCR。现有测试不能证明更换 OCR 模型后真实验证码识别行为不变。

来源：

- [Python 官方版本状态](https://devguide.python.org/versions/)
- [Python 3.10 生命周期 PEP 619](https://peps.python.org/pep-0619/)
- [ddddocr 1.4.11 元数据](https://pypi.org/project/ddddocr/1.4.11/)
- [ddddocr 1.6.1 元数据](https://pypi.org/project/ddddocr/1.6.1/)

**兼容性决策推荐：**

- 第一轮 P4 不升级 ddddocr 1.4.11。
- 将下一正式版本的 Requires-Python 收窄为 `>=3.11,<3.12`，classifier 只保留 Python 3.11；不再声称支持已经 EOL 的 3.10，也不让 3.12+ 用户在安装阶段获得错误预期。
- 如果维护者希望扩展到 3.12+，先单独验证 ddddocr 1.6.1 或更高版本，并准备经批准的非敏感 OCR fixture。没有 fixture 或识别回归不通过时，停止升级，不把单纯 import 成功视为兼容。
- Python 3.11 EOL 前必须重新评估 OCR 依赖迁移；建议最晚于 2027-04-01 启动复核。若届时仍无可验证的 OCR 兼容方案，不应继续扩大 Python 支持声明。

### 2.5 当前 CI、测试与文档

| 文件/流程 | 当前事实 | P4 影响 |
| --- | --- | --- |
| `tox.ini` | tox 4；`py311-cover`；check、docs、coverage | Python 3.11 是唯一实际测试版本 |
| `.github/workflows/github-actions.yml` | Ubuntu；check、docs、py311-cover、finish | 保留当前必需 Build 流程 |
| `.github/workflows/offline-tests.yml` | Docker build 后以 `--network none` 运行完整测试；导出 JUnit、coverage、tox 和网络证据 | P0–P3 核心安全网必须保留 |
| `ci/offline.Dockerfile` | `python:3.11-bookworm`；依赖在镜像构建阶段准备 | 与 Python 3.11 首轮支持范围一致 |
| `ci/run_offline_tests.py` | 使用 `.tox/py311-cover/bin/python` | 当前无需为了未经批准的多版本矩阵而扩大改动 |
| `ci/requirements.txt` | 已含 tox、twine、pip 等；没有 build frontend | 如采用 `python -m build`，需增加 build 工具 |
| `.readthedocs.yml` | Python 3.10；`formats: []`；安装项目和 docs requirements | 将构建 Python 改为已验证的 3.11；保留 HTML-only |
| `docs/requirements.txt` | Sphinx 7.2.6 | 暂不升级 Sphinx |
| `tox docs` | HTML build 后执行在线 linkcheck | 必须区分 HTML 构建与需要外网的 linkcheck |
| `.github/workflows/document.yml` | tag 触发；构建后发布 GitHub Pages | 与 README/包元数据指向的 Read the Docs 存在双发布目标 |
| `.github/workflows/release.yml` | 任意 tag `*` 触发；checkout `@master`；setup-python v3 / Python 3.10；`setup.py sdist bdist_wheel`；PyPA OIDC 发布 | 目前发布触发过宽，且发布前没有明确的同 SHA Build/Offline gate |

P4 不得移除或弱化 Offline tests 的系统级禁网、父环境凭证隔离、三种测试入口、完整 JUnit、coverage 和 Artifact 收集。P3 的 467 项是历史基线，P4 的最终提交仍须重新执行。

## 3. 维护者决策与默认推荐

以下决策会改变公开兼容承诺或发布权限，Plan 先给出建议，Build 前必须由维护者确认。

| 决策 | 推荐选项 | 备选与停止条件 |
| --- | --- | --- |
| 下一版本 | `0.3.0` | 如果维护者认为 P0–P3 只是补丁修复，可另议 0.2.7；不得在计划中擅自改版本 |
| Python | 3.11 only；`>=3.11,<3.12` | ddddocr 升级并有 OCR fixture 后再扩展；没有证据不得写 3.12+ |
| OS | Linux / CPython 已验证 | Windows/macOS 只有增加真实 CI 证据后才可声明 |
| ddddocr | 首轮保留 1.4.11 | 1.6.1 作为独立兼容性实验，不与首轮发布强绑定 |
| Beta | PyPI `0.3.0b1` | 可改 GitHub Pre-release；不得自动公开发布 |
| 文档主站 | Read the Docs | 若 GitHub Pages 仍被实际使用，明确其 mirror 角色；否则停止重复部署 |
| 发布权限 | `pypi` environment required reviewer + OIDC | 若仓库环境未配置保护，先完成设置，不得用长期 PyPI token 绕过 |
| 真实账户验证 | 不需要、不纳入 P4 | 任何真实只读/写入验证都必须另行单独授权 |

### 3.1 为什么建议 0.3.0

从 0.2.6 到当前 master，项目已完成 P0 安全基线、P1 离线测试隔离、P2 新增 TradingClient 公共 API、P3 新增 TradeOutcomeUnknown / BrokerHTTPError 失败语义。旧九项模块级 API 和 CLI 的兼容契约保留，但对外新增了明确的客户端和异常接口。

建议以 0.3.0 作为这批已完成变更的首次正式交付，并使用 PEP 440 的 alpha/beta/rc 预发布序列。版本选择是建议，不是发布授权。

### 3.2 首轮 Python 3.11 only 的代价

此选择意味着新版本在 PyPI 上的安装范围较窄，无法满足 3.12+ 用户；但它能准确表达当前固定 OCR 依赖实际可安装的边界，并避免未经验证地改变验证码识别引擎。

这不是长期理想状态。P4 可先关闭“声明真实、产物可安装、发布可审计”这一目标；OCR 引擎升级和 Python 3.12+ 支持作为有明确验证前置条件的后续事项。若维护者不接受仅支持 3.11，应暂停正式发布，先单独完成 OCR 兼容性验证。

## 4. 目标发布流程

~~~text
PR / merge to master
        |
        v
Build + check + docs HTML
        |
        +----------------------+
        |                      |
        v                      v
Offline tests             Package build
network=none              sdist + wheel
        |                      |
        +-----------+----------+
                    |
                    v
          Package install smoke
          in fresh environments
          runtime network=none
                    |
                    v
             Alpha artifacts
             internal review
                    |
                    v
          Beta version / approval
                    |
                    v
       exact artifact + SHA256 manifest
                    |
                    v
       protected PyPI environment approval
                    |
                    v
       Trusted Publishing OIDC / PyPI
                    |
                    v
       post-publish hash + provenance check
                    |
                    v
       GitHub Release + docs publication
~~~

核心原则：

- PR 阶段只验证，不发布。
- tag 阶段先构建并验证，不因 tag 创建自动获得发布授权。
- Build 和 Offline tests 必须对应同一最终提交 SHA。
- sdist/wheel 只构建一次；Publish job 下载并发布相同 Artifact，不在发布 job 重新构建。
- OIDC 只在 Publish job 开启；其它 job 仅有读取权限。
- PyPI 版本不可覆盖；上传结果不确定时先查询实际版本和 SHA256，不盲目重试。

## 5. 分阶段实施步骤

### S0 · 只读基线与决策锁定

**目标：** Build 开始前重新锁定事实，避免使用过期分支、tag 或包元数据。

执行：

1. 记录 master、P4 branch 的真实 HEAD、Tree、工作区状态和 P4 requirements blob。
2. 重新读取 setup.py、pyproject、tox、CI workflows、Read the Docs config、Changelog、README、公开 API 契约和 P0–P3 最终验收报告。
3. 查询 Git tags、GitHub Releases、PyPI 当前版本、Requires-Python、classifiers、文件 SHA256 和 provenance。
4. 检查 GitHub `pypi` environment 是否存在 required reviewers；如连接器权限无法读取设置，列为维护者手动检查项。
5. 确认文档主站；核实 GitHub Pages 是否有外部使用者。
6. 维护者批准版本号、Python 范围、Beta 渠道和发布审批规则。

验收：

- S0 输出的基线 SHA、PyPI 版本、依赖限制和发布配置均有原始来源。
- 没有修改任何仓库文件。
- 任一关键事实无法核实时，记录未知，不按猜测推进。

### S1 · Python / OCR 依赖 Kill Test

**目标：** 证明拟声明的 Python 范围与依赖元数据一致。

首轮推荐方案：

1. 在 Python 3.11 干净环境执行依赖解析和安装，确认现有锁定依赖可用。
2. 在 Python 3.12 环境用现有 ddddocr 1.4.11 做 metadata / resolver 检查，记录其 `Requires-Python <3.12` 阻断证据；不通过修改 pip 参数绕过元数据。
3. 检查 ddddocr 1.6.1 的依赖、API、模型文件和许可证；只在隔离实验环境安装，不改项目运行依赖。
4. 盘点是否存在经批准、非敏感、可重复的验证码图片 fixture。当前 `tests/fixtures` 只有合成协议 JSON，不能作为 OCR 识别回归集。
5. 若没有 fixture，不升级 ddddocr，不宣称 Python 3.12+；将首轮 Requires-Python 收窄到 `>=3.11,<3.12`。
6. 若未来获得合格 fixture，另行执行旧版/候选版模型输出对照、模型加载、错误处理和依赖安装矩阵；此实验不执行真实登录。

Kill 条件：

- Python 3.11 依赖安装失败：停止版本/发布阶段，先修复依赖问题。
- 3.12+ 依赖 resolver 失败：不能声明该版本支持。
- 候选 ddddocr 模型输出变化但没有可信 fixture 解释：停止升级。
- 不允许为了扩大矩阵而把失败测试标成 allowed failure 后仍宣称支持。

### S2 · 版本、包元数据与文档一致性

**目标：** 使包版本、安装范围、Changelog、文档和 Git tag 一致。

建议修改：

1. 将 Requires-Python 更新为维护者批准的范围；按首轮建议为 `>=3.11,<3.12`。
2. Python classifiers 只声明实际验证版本；首轮仅 Python 3.11。
3. OS classifier 收窄到实际验证的平台；首轮建议 Linux，不宣称 Windows/macOS。
4. 检查 `src/emtl/__init__.py`、setup.py fallback、setuptools_scm 生成版本、docs/conf.py 和 .bumpversion.cfg 一致。
5. 使用 bumpversion 时必须显式 `--no-commit --no-tag`；人工检查 diff 后才允许正常提交。禁止直接运行当前默认会 commit/tag 的配置。
6. 更新 `CHANGELOG.rst`，将 P0–P3 的用户可见变化整理为 release notes：安全日志/CLI 修复、离线测试安全网、TradingClient、TradeOutcomeUnknown / BrokerHTTPError、旧 API 兼容边界和未验证真实券商协议的限制。
7. 更新 README、Installation、Contributing、reference docs 和包 metadata 的 Python/OS 支持声明。
8. `.readthedocs.yml` 的 Python 从 3.10 改为已验证的 3.11；继续 `formats: []`，不提供 PDF/EPUB。
9. `docs/conf.py` 不应在正常 HTML 构建中因 metadata 缺失打印完整 traceback；仅做最小安全回退，避免重写 Sphinx 配置。
10. 先确认 Read the Docs 与 GitHub Pages 的实际职责。默认以 Read the Docs 为官方入口；若 GitHub Pages 没有明确用途，停止重复部署；若保留，则在 README 和项目 metadata 中标明 canonical 与 mirror。

验收：

- 所有版本字段与 tag 对应。
- PyPI metadata、README、安装文档和 classifier 一致。
- HTML Sphinx build 通过；无 PDF/EPUB 构建。
- 没有未批准的 API、CLI、交易行为变化。

### S3 · Alpha 包构建与安装验证

**目标：** 对最终 sdist/wheel 做真实的干净环境安装，而不是只在源码 checkout 下 import。

推荐构建方式：

~~~bash
python -m pip install -r ci/requirements.txt
python -m build --sdist --wheel --outdir dist/release
python -m twine check --strict dist/release/*
~~~

如采用 `python -m build`，在 CI 工具依赖中增加 `build`；不因此迁移到 PEP 621 或重写 setup.py。

产物检查：

1. sdist 和 wheel 的版本、Requires-Python、Requires-Dist、entry points、license、README/Changelog 一致。
2. wheel 中包含必要的 emtl package 文件和 setuptools_scm 生成版本文件。
3. sdist 可以在没有 Git metadata 的干净目录中构建出相同版本；不能依赖开发机 .git 或遗留 dist/。
4. 不包含 tests、CI 临时输出、coverage、缓存、真实秘密、开发机绝对路径或未授权数据。
5. 为每个产物生成 SHA256、文件清单和构建工具版本报告。

**干净安装验证：**

- sdist 和 wheel 分别安装到两个独立的 Python 3.11 venv。
- 两个环境分别执行 `pip check`。
- 在安装后验证 `emtl.__version__ == importlib.metadata.version("emtl")`，并与预期 tag version 完全一致。
- 验证 `import emtl`、`from emtl import TradingClient`、`from emtl.errors import TradeOutcomeUnknown, BrokerHTTPError`。
- 验证既有九个包级函数、CLI entry point、`emt --help`、`python -m emtl --help`。
- 构造合成凭证的 TradingClient 后立即 close；不得调用 login 或任何交易方法。

**系统禁网要求：**

包安装和依赖准备发生在独立 Docker image build 阶段；所有 smoke test 在容器以 `--network none` 启动后执行。推荐新增最小 `ci/package_smoke.py` 与 `ci/package-smoke.Dockerfile`，或证明可以无损复用现有 offline Docker 结构。

不能只在允许联网的 GitHub runner 上执行 smoke test，然后称其为系统级禁网验收。

Kill 条件：

- sdist/wheel 版本不一致。
- 安装依赖与 Requires-Python 冲突。
- CLI/import 构造触网。
- 缺失公开 API 或 entry point。
- 包产物包含秘密或测试材料。

任一项失败，不进入 Beta。

### S4 · Alpha 内部验证

Alpha 不上传 PyPI，不创建正式 tag，不对外宣称生产可用。

Alpha 验收：

- S3 两种产物均通过。
- P0–P3 全部既有测试和当前 Linux Offline tests 通过。
- `tox -e check` 和 Sphinx HTML build 通过。
- 产物 SHA256、文件清单、版本、依赖、smoke 输出可追溯。
- 独立 Review 检查 Requirements、Plan、产物内容和交易安全边界。
- 任何异常、安装失败或版本不一致都先修复，不通过降低测试强度解决。

Alpha 输出：内部候选版本、完整测试证据、已知限制和 Beta 准入结论。

### S5 · Beta 验证

**推荐：** 维护者批准后，将 `0.3.0b1` 作为 PyPI pre-release；保留当前 PyPI Trusted Publishing。用户显式安装，不替换默认稳定版本。

安装示例：

~~~bash
python -m pip install --pre emtl==0.3.0b1
~~~

Beta 发布说明必须包含：

- 版本、日期、Python 3.11 / Linux 适用范围。
- 本次新增 API、异常语义和兼容说明。
- 已知限制：真实券商协议未由自动测试验证；Unknown 不代表成交或拒绝；不自动重试。
- 反馈模板：Python/OS/安装方式、最小复现、脱敏异常和预期/实际结果。
- 明确禁止提交密码、验证码、token、Cookie、账户标识、完整请求/响应和交易记录。

Beta 测试只要求：

- 安装、导入、版本、CLI help、文档和合成离线调用。
- 用户反馈的安装/API 问题。
- 不要求用户提供真实账户或真实交易结果。
- 不把没有收到反馈当成真实协议验证通过。

建议 Beta 观察窗口为 10 个工作日；若没有有价值的外部反馈，维护者必须显式选择继续观察、直接发布或暂停，不无限延长。

Beta 退出条件：

- 没有未解决的高严重度安装、版本、敏感信息或交易风险缺陷。
- 反馈已分类，阻断问题已修复或延期且有明确披露。
- 同一批产物的 SHA256 与待发布产物一致。
- 维护者明确批准进入 Stable。

### S6 · 正式发布工作流

**当前问题：** release.yml 对任意 tag `*` 触发发布；使用 `actions/checkout@master`、`actions/setup-python@v3` 和旧版 setup.py 构建；发布前没有明确要求同一 SHA 的 Build/Offline tests 通过。

建议最小调整：

1. tag 触发限制为 `v*`，并用 Python packaging 解析验证 tag 符合版本格式；拒绝任意非版本 tag。
2. 验证 tag 指向已合并到 master 的提交；禁止从未合并分支或 PR head 直接发布。
3. 验证 tag version、setuptools_scm version、wheel metadata、sdist metadata 和 `emtl.__version__` 一致。
4. 发布前确认该 commit SHA 对应的必需 Build、check、docs HTML 和 Offline tests 均成功。不能拿 PR head 的成功结果替代 master merge commit 的检查；需要核对精确 SHA。
5. Build job 使用 `actions/checkout@v4`、`actions/setup-python@v5` 或经审查的更新版本；不再使用 `checkout@master`。
6. Build job 仅有 `contents: read`；不授予 `id-token: write`。
7. 构建一次 sdist/wheel，上传 `actions/upload-artifact@v4`，包含 SHA256 manifest、构建版本、文件清单和检查结果。
8. Package smoke job 下载同一 Artifact，在禁网容器中分别安装和运行测试；不重新构建包。
9. Publish job 下载相同 Artifact；只在该 job 配置 `id-token: write`，使用现有 PyPI Trusted Publishing，不新增长期 PyPI token。
10. Publish job 使用 `environment: pypi`；必须在 GitHub Settings 确认该 environment 配有 required reviewers。若没有保护，先配置，不能将 environment 名称存在当作审批已启用。
11. PyPA publish action 应锁定到经核实的完整 commit SHA；其它第三方 action 按安全维护策略锁定版本。
12. 对 pre-release 与 stable release 使用明确条件；`0.3.0a1` / `0.3.0b1` 不得意外触发稳定版文档或稳定版发布步骤。
13. 不使用 `skip-existing` 掩盖上传冲突。上传状态不确定时先查 PyPI 已存在版本和文件哈希，再决定是否继续。
14. 发布后核对 PyPI 文件 SHA256、provenance、项目版本页和安装 smoke test。

PyPI OIDC 与 provenance 继续沿用当前 Trusted Publishing 路线；不增加个人 API token、仓库长期 secret 或真实账户秘密。

### S7 · 文档发布

默认选择 Read the Docs 为官方文档入口，原因是 README 和 setup.py project_urls 已指向 `https://emtl.readthedocs.io/`，且 `.readthedocs.yml` 已存在。

执行：

1. `.readthedocs.yml` Python 3.10 改为已验证的 3.11。
2. 保持 `formats: []`；只构建 HTML。
3. Required docs CI 只负责 Sphinx HTML 构建。
4. 在线 `linkcheck` 与 HTML 构建分离；linkcheck 可作为独立 job / 定时检查，不得把网络抖动混成包测试失败。
5. 确认 Read the Docs 对 master、tag 和预发布版本的构建行为。
6. 检查 `document.yml` 发布 GitHub Pages 是否仍有必要。若保留，必须说明 mirror 与 canonical 的关系；若无真实使用者，移除重复发布工作流并统一文档链接。
7. Release notes、README、Installation、API reference、Changelog 的版本和支持矩阵一致。

### S8 · 持续维护

维护机制保持轻量：

1. 新增 `SECURITY.md`，说明私密安全问题报告路径；确认 GitHub Private Vulnerability Reporting 是否可用，不要求用户在公开 Issue 上传日志或凭证。
2. 新增 `.github/dependabot.yml`，每月检查 pip 和 GitHub Actions 更新；自动 PR 不自动合并。
3. 对 requests、urllib3、cryptography、rsa、ddddocr 等可能影响认证、HTTP 和交易行为的依赖更新，必须经过定向请求次数、重定向、异常、OCR 和 Offline tests 回归。
4. 不以“最新版本”为由整体升级依赖；每个升级说明安全/兼容原因、版本差异、风险和回滚方式。
5. 每月或有重要安全公告时检查依赖；没有必要不引入 pip-audit 服务或新的 SaaS。
6. 支持政策：只对当前 stable 版本承诺正常维护；旧版本 best effort；不承诺没有资源保障的 SLA。
7. Issue 分类为安全、交易风险、功能、兼容、安装、文档和依赖；安全问题不在公开 Issue 中索要秘密。
8. Python 3.11 支持到期前复核；建议 2027-04-01 前完成 ddddocr / Python 3.12+ 方案评估。

## 6. 可执行验收命令

以下命令是实施阶段的验收模板，不代表本次已运行。

### 6.1 当前 Python 3.11 测试基线

~~~bash
python -m pytest -p no:cacheprovider -vv
tox -e py311-cover -v
tox -e check -v
~~~

系统级 Linux 禁网仍通过既有 Docker 流程执行：

~~~bash
docker build -f ci/offline.Dockerfile -t emtl-p4-offline .
docker create --name emtl-p4-offline-run --network none emtl-p4-offline
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p4-offline-run
docker start --attach emtl-p4-offline-run
docker inspect --format '{{.State.ExitCode}}' emtl-p4-offline-run
~~~

实际脚本应保留现有 workflow 的 trap、报告导出、容器退出状态、清理状态和 Artifact 收集逻辑；不能用上述简化命令替代现有证据驱动。

### 6.2 构建和产物检查

~~~bash
python -m build --sdist --wheel --outdir dist/release
python -m twine check --strict dist/release/*
python -m pip check
~~~

分别安装 sdist 和 wheel 到全新 venv；安装完成后检查：

~~~bash
python -c "import emtl; from importlib.metadata import version; print(emtl.__version__, version('emtl'))"
python -c "from emtl import TradingClient"
python -c "from emtl.errors import TradeOutcomeUnknown, BrokerHTTPError"
emt --help
python -m emtl --help
~~~

smoke runner 必须比较实际版本与传入的 expected version；不能只打印版本后人工目测。

### 6.3 文档

~~~bash
sphinx-build -E -b html docs dist/docs
~~~

HTML build 与在线 linkcheck 分开执行。最终远端 Read the Docs 构建必须对应目标 tag/commit。

### 6.4 发布前元数据和 SHA

对 sdist、wheel 分别计算 SHA256，生成 manifest；发布前后逐文件比较。发布后通过 PyPI 页面/JSON 读取实际上传文件哈希，并核验 provenance 绑定的 repository、workflow 和 commit。

## 7. 预期修改文件清单

以下是 Build 获批后的候选清单；Plan 阶段不修改它们。最终以 S0 复核后的最小 diff 为准。

| 文件 | 预期用途 | 是否触及交易运行逻辑 |
| --- | --- | --- |
| `setup.py` | Python 范围、classifier、依赖策略、包构建元数据 | 否；但依赖版本变更可能影响 OCR/HTTP |
| `src/emtl/__init__.py` | 版本字符串同步 | 仅版本常量，不改 API 行为 |
| `.bumpversion.cfg` | 版本更新规则和人工 tag/commit 边界 | 否 |
| `README.rst`、`CHANGELOG.rst` | 安装范围、发布说明、兼容限制 | 否 |
| `docs/conf.py`、`docs/installation.rst`、`docs/reference/emtl.rst`、`CONTRIBUTING.rst` | 文档和维护说明 | 否 |
| `.readthedocs.yml` | 文档构建 Python 版本 | 否 |
| `ci/requirements.txt` | 仅在采用 build frontend 时增加构建工具 | 否 |
| `tox.ini` | 将 HTML build 与在线 linkcheck 分离（如确认有必要） | 否 |
| `.github/workflows/release.yml` | 构建/验证/审批/发布拆分、tag 校验和 OIDC 最小权限 | 否 |
| `.github/workflows/document.yml` | 文档发布职责和 tag 过滤 | 否 |
| `.github/workflows/github-actions.yml` | 仅在需要拆分 docs 或验证发布 SHA 时调整 | 否 |
| `ci/package_smoke.py` | 安装后 API、版本、CLI、无副作用 smoke tests | 否 |
| `ci/package-smoke.Dockerfile` | 依赖预装后，在 network none 下测试安装产物 | 否 |
| `tests/test_package_metadata.py` | Requires-Python、版本和 metadata 契约 | 否 |
| `SECURITY.md`、`.github/dependabot.yml` | 安全报告与依赖更新流程 | 否 |

**明确不在首轮 P4 修改清单：**

- `src/emtl/core.py`、`src/emtl/client.py`、`src/emtl/_protocol.py`、`src/emtl/errors.py` 的交易、认证、异常和 HTTP 行为。
- P0–P3 现有测试断言、fixtures、账户锁和禁网 guard。
- endpoint、表单字段、验证码算法、订单参数、交易重试或自动恢复。
- 不必要的依赖大版本升级、async、分布式锁、数据库、队列或新的 SaaS。

若 S1 最终批准 ddddocr 升级，则必须先单独调整生产依赖，并增加可验证 OCR fixtures；这属于明确批准的高风险例外，不自动包含在首轮文件修改中。

## 8. 发布失败、回滚和 Hotfix

### 8.1 不允许的回滚假设

PyPI 现有 `0.2.6` 早于 P0–P3。该版本没有当前已完成的安全日志、离线测试隔离、TradingClient 多账户边界和 P3 交易结果未知异常契约。

因此：

- 不把 `pip install emtl==0.2.6` 作为自动或默认安全回滚命令。
- 不因 0.3.0 安装失败就建议用户无条件降级到 0.2.6 并继续真实交易。
- 0.2.6 可作为历史版本保留，但必须明确其安全与兼容差异。

### 8.2 处理规则

| 事件 | 处理 |
| --- | --- |
| 构建/测试失败 | 不创建正式 tag，不发布 |
| 上传前发现产物错误 | 修复后重新构建，生成新候选并重新验证 |
| PyPI 上传状态不确定 | 查询 PyPI 实际版本、文件列表和 SHA256；禁止盲目重复上传 |
| 已发布版本有普通缺陷 | 暂停推荐该版本，评估 yanking，发布新的唯一 Hotfix 版本 |
| 已发布版本有交易/安全风险 | 立即发布风险说明，要求用户停止受影响操作；优先修复前进，不自动重发/补偿订单 |
| GitHub Release 说明错误 | 修正 Release notes；不能重用或覆盖 PyPI 文件 |
| docs 发布失败 | 修复文档部署，不以重新发布相同 PyPI 版本解决 |

### 8.3 Hotfix

- 从明确的已发布版本/修复基线创建分支。
- 增加针对缺陷的最小失败测试。
- 运行完整 Offline tests、Build、包安装和 smoke tests。
- 使用新版本号（例如 0.3.1），不覆盖 0.3.0。
- 需要时在 PyPI 手动 yank 受影响版本；yank 不是删除，也不会撤销用户已经安装的软件。
- 回滚 SDK 不能撤销券商已经接受的订单或资金变化；不实现自动补偿。

参考：[PyPI yanking](https://docs.pypi.org/project-management/yanking/)。

## 9. 风险、Kill Test 与停止条件

| Kill Test | 最低证据 | 失败后的动作 |
| --- | --- | --- |
| K1 Python 依赖解析 | 3.11 干净安装通过；3.12+ 当前 ddddocr 限制被准确识别 | 不扩大 Python 声明 |
| K2 OCR 升级 | 候选 ddddocr API/模型与批准 fixture 回归一致 | 无 fixture 或结果不一致时停止升级 |
| K3 版本一致性 | tag、SCM、wheel、sdist、runtime __version__ 完全一致 | 不生成 Beta |
| K4 包完整性 | sdist/wheel 均可独立安装，pip check 通过 | 不生成 Beta |
| K5 网络副作用 | CLI help、import、构造客户端在 OS-level network none 下通过 | 不发布 |
| K6 产物秘密扫描 | 包清单与候选产物无凭证、Cookie、Token、真实账户数据 | 删除产物并重新构建 |
| K7 Release trigger | 非版本 tag、非 master commit、未通过 CI、无审批时发布 job 必须 fail closed | 不允许上线 |
| K8 同一 Artifact | 测试的 SHA256 与 Publish 下载的 SHA256 完全一致 | 不允许发布 |
| K9 PyPI provenance | 发布文件对应预期 repository、workflow、commit | 停止后续 release 宣称 |
| K10 文档支持范围 | README、PyPI metadata、RTD、Changelog 的 Python/OS 声明一致 | 不关闭 P4 |

其他停止条件：

- 任何 P0–P3 测试被删除、skip、xfail 或弱化以适应 P4。
- 任何自动真实登录、交易 POST、自动重试、自动补单、自动确认或补偿操作。
- Release job 能绕过 required reviewer 或在 PR 上获得 OIDC 发布权限。
- tag 与版本、受测 SHA、Artifact 不一致。
- 0.2.6 被描述为 P0–P3 的安全回滚版本。
- 继续增加测试矩阵、工具或自动化平台，却没有改变兼容性结论或发布风险。

## 10. P4 最终验收矩阵

| 领域 | PASS 必需证据 |
| --- | --- |
| 需求与计划 | 本文件获维护者批准；每个决策有明确结论 |
| Python/依赖 | Requires-Python 与 ddddocr metadata 一致；每个声明支持版本有真实 CI 证据 |
| OS | classifier 与实际验证平台一致；不宣称未测 OS |
| Alpha | sdist/wheel 构建、内容检查、干净安装、版本、API/CLI smoke 均通过 |
| Beta | 候选说明、反馈窗口、问题分类、退出决策和人工批准有记录 |
| Build CI | check、docs HTML、coverage 和必需工作流通过 |
| Offline tests | 系统 NetworkMode=none；完整 JUnit、coverage、tox、版本和 Artifact 证据 |
| 发布权限 | tag 校验、master 祖先校验、同 SHA CI、protected pypi environment、OIDC 最小权限 |
| Artifact | Build 一次；smoke 与 Publish 使用同一产物；SHA256 一致 |
| PyPI | sdist/wheel 文件存在、哈希一致、provenance 可核验 |
| 文档 | RTD HTML 构建成功；canonical/mirror 职责明确；无 PDF/EPUB |
| 回滚 | 0.2.6 风险明确；yank/Hotfix/前进修复步骤可执行 |
| 持续维护 | SECURITY.md、Dependabot、Issue 分类和依赖审查触发条件明确 |
| 独立 Review | 审查最终 requirements、approved plan、所有 diff、构建产物、权限和证据；PASS |
| 阶段关闭 | 最终提交远端双工作流/Artifact/Tree 与本地候选对应；维护者批准关闭 |

覆盖率、测试数量、workflow 数量和 Beta 下载量均不能单独作为 P4 PASS 依据。

## 11. Build 批次与回滚方式

| 批次 | 修改范围 | 验收后才进入下一批 | 回滚方式 |
| --- | --- | --- | --- |
| B0 | 只读基线与决策记录 | S0 决策完成 | 无文件修改 |
| B1 | Python Requires-Python、classifier、依赖边界 | S1 Kill Test 通过 | revert metadata/doc commit |
| B2 | 版本、Changelog、README、RTD 和 docs | 版本一致性、HTML build | revert docs/metadata commit |
| B3 | 包构建、安装 smoke、Artifact SHA | sdist/wheel 均通过 | 删除候选 Artifact，重新构建 |
| B4 | Release workflow 和环境权限 | K7/K8 通过；不触发真实 publish | revert workflow commit；保持 OIDC 不可用 |
| B5 | Alpha / Beta | Alpha/Beta 退出条件满足 | 停止 Beta，撤下候选说明；不覆盖 PyPI 文件 |
| B6 | Stable release | 单独人工批准并完成远端核验 | yank + 新版本 Hotfix，不覆盖旧版本 |
| B7 | SECURITY、Dependabot、维护文档 | Review PASS | revert 维护配置，不影响已发布包 |

每批独立 commit，禁止一次性大改后只跑全量测试。Build agent 不得自动 commit/push/merge/tag 或发布；由维护者控制 Git 和 release 动作。

## 12. 独立 Review 清单

Reviewer 必须使用独立 Session，读取 Requirements、批准 Plan、最终 Git diff、tracked/staged/untracked、包产物、远端 CI 和 PyPI 元数据。

至少回答：

1. Requires-Python 是否被 ddddocr 实际元数据约束？是否出现未验证的 Python/OS 支持声明？
2. ddddocr 是否被未经 OCR fixture 验证就升级？
3. `emtl.__version__`、distribution metadata、SCM tag、sdist/wheel 是否一致？
4. sdist 与 wheel 是否分别在干净 venv 安装？是否检查了依赖和 CLI entry point？
5. import、help、客户端构造是否在 network none 下完成？
6. P0–P3 的 467 项历史保护是否继续存在，是否有任何删除/skip/弱化？
7. Offline tests 是否继续是系统级禁网，而非只有 pytest monkeypatch？
8. Release workflow 是否能从任意 tag、PR 或未通过 CI 的提交发布？
9. OIDC 是否只在 Publish job，且 pypi environment 是否真实配置 required reviewers？
10. 测试产物与发布产物 SHA256 是否完全一致？
11. PyPI provenance 是否对应预期 repository、workflow 和 commit？
12. 文档是否只有一个明确 canonical 入口，且 HTML build 与在线 linkcheck 分离？
13. 是否错误地建议回滚到缺少 P0–P3 的 0.2.6？
14. 是否出现自动真实账户请求、重复交易或自动恢复行为？

Reviewer 输出必须为：

- `PASS`：所有高风险断言有最终版本证据。
- `FAIL`：存在明确的兼容、秘密、发布权限或交易安全问题。
- `NEEDS EVIDENCE`：缺少远端 CI、Artifact、PyPI provenance 或人工权限证据。

本地 Build 自评不能替代独立 Review。

## 13. 需要维护者批准的事项

Build 开始前，至少确认：

1. 是否采用 `0.3.0` 作为下一稳定版本。
2. 是否接受首轮仅支持 Python 3.11，并将 Requires-Python 收窄为 `>=3.11,<3.12`。
3. 是否暂时保留 ddddocr 1.4.11，待有 OCR fixture 后另立依赖升级阶段。
4. Beta 使用 PyPI `0.3.0b1` 还是 GitHub Pre-release。
5. Read the Docs 是否作为唯一 canonical docs，GitHub Pages 是否仅作为 mirror 或停止部署。
6. GitHub `pypi` environment 是否启用 required reviewers。
7. Stable PyPI 发布是否在 Beta 后另行单独批准。
8. 是否提供任何经批准的非敏感 OCR fixture；没有则不进行 OCR 依赖升级。

这些决策没有批准时，可以完成只读调查和 Alpha 计划细化；不得擅自扩展兼容范围或发布。

## 14. P4 结束与停止条件

全部满足后才宣布 P4 PASS：

- Python/OS/依赖声明与实际可安装和 CI 证据一致。
- sdist、wheel 均能在干净环境安装并通过 smoke tests。
- Alpha/Beta 按批准方式完成，阻断反馈关闭或明确延期。
- Release workflow 对 tag、版本、master commit、CI、Artifact SHA 和审批 fail closed。
- PyPI 发布使用 Trusted Publishing，产物 provenance 可核验。
- Read the Docs HTML、README、Changelog 和 PyPI metadata 一致。
- 失败处理、yank、Hotfix、维护责任和安全报告流程有明确步骤。
- P0–P3 资金风险和离线安全断言未弱化。
- 最终远端 CI、Artifact、Tree 和独立 Review 证据闭环。

完成后停止 P4，不为了追求更多 Python/OS 矩阵、更多自动化平台或更高覆盖率继续扩大范围。Python 3.12+ 与 ddddocr 升级如果仍无可靠 OCR 验证证据，保留为明确的后续风险，不用未经验证的支持声明掩盖。
