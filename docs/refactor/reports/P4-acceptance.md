# P4 Build 与阶段验收记录

> **当前 P4 收尾代码基线（2026-11-09）：** PR #23 已合并到 master，merge commit `d5eb7d71e4b65fb28e0398b64269a9d1225c833a`，tree `f9d361cec8d5a23e2f3b6576efbc63d915250633`。PR head `66d3a3b58b55ba047bef595f497874c7fd619c88` 与 merge commit 的 tree 完全一致；最终 master push 的 Build、Offline tests、Package Alpha 均已在 merge SHA 上成功。详情见本文末尾“PR #23 合并后最终 master 验证”。**P4 阶段整体仍为 NEEDS EVIDENCE**：no-upload 审批探针和 Beta 观察/退出尚未闭环；RTD HTML 验收由维护者确认通过，但本轮未取得独立 Build ID。未创建 tag、未上传 PyPI、未执行正式发布。



## 授权与当前状态

- 日期：2026-11-08；分支 `refactor/p4-release-maintenance`。
- 最终收尾复验：2026-11-09（服务重启后继续；启动已有 Colima 实例，未创建新 VM/修改远端配置）。
- 开始 HEAD：`038e1fdc031a5be6cbe277a48913e0c6d3230863`；tree：`341c0393ddc1c8ab8f821948ab3f956e0b6b959c`。开始 tracked/staged/untracked 均干净。
- 维护者批准的决策及范围见 [P4-plan](../plans/P4-plan.md) §1 的追加记录；仅本地实施，不 commit/push/tag/上传/发布，不执行真实账户验证。
- **状态：本地实现与回归已完成，P4 总体 NEEDS EVIDENCE；公开 Beta/Stable 仍 BLOCKED。** 不用本地结果代替独立 Review、远端 CI、Beta 退出或发布授权。

## S0 只读核实

- `git ls-remote origin`：master `225d4e59c9689ed7414a2f0aa9d0a1c7ac8c8fbb`；P4 branch 为开始 HEAD；最新 tag `v0.2.6` 指向 `89328a75ea42362587fb46e6a9f395d0ca90ee86`。
- requirements blob：`be5d5529263b3c2baeaee046dc8655e4aae34d7d`；本地 master、origin/master 与远端一致。
- `gh api repos/riiy/emtl/releases`：空列表。
- `gh api repos/riiy/emtl/environments/pypi`：`{"name":"pypi","protection_rules":[]}`。审批保护未配置，属发布阻断项；不修改远端设置。
- Docker daemon 可用（29.5.2）；本机有 uv 管理的 CPython 3.11.14 / 3.12.12。自动测试继续使用系统禁网与合成数据。

## 批次测试与依赖证据

- 改动前：`PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -q --junitxml=dist/p4/baseline-junit.xml`，退出 0，**467 passed**。
- B1 先行契约：同一禁网前缀执行 `tests/test_package_metadata.py`，1 failed / 1 passed，失败为原 Requires-Python `>=3.10` 与批准范围不符（预期红灯）。
- 宿主机 Python 访问 PyPI 因 DNS 失败；改在独立 Docker 准备环境只读获取公开元数据，`emtl 0.2.6` 仍为当前稳定版；ddddocr 1.4.11 要求 `<3.12`，1.6.1 要求 `>=3.10`，许可证 MIT，后者依赖 numpy/onnxruntime/Pillow/opencv，不做 OCR 引擎升级。
- 原始公开元数据保存 `dist/p4/baseline/*.json`。完整依赖在线安装超过工具等待上限，后续下载仍缓慢；停止本次创建的容器，未将它当作通过。首次离线缓存安装缺 flatbuffers wheel（缓存不完整，不是兼容性证明），已保存失败日志。改为准备公开 wheel 缓存，然后在全新 venv、`--network none` 下重跑。
- S1 最终：缓存 wheel 重建脚本最初误用 py2.py3 wheel 的首个 py2 tag，导致遗漏 flatbuffers；改为选择实际兼容 tag 后，Python 3.11 的全新 venv 禁网安装成功，`pip check` 退出 0，freeze 记录全部传递依赖。未改变项目依赖版本。
- pip 旧版的 `--python-version 3.12` 模拟先因缺少 3.12 numpy wheel 失败，不能作为 ddddocr 阻断证据。改用真实 CPython 3.12.12 新 venv、pip wheel 及 macOS 系统禁网执行 `pip install --dry-run --no-deps --no-index --find-links=dist/p4/baseline/wheels ddddocr==1.4.11`，退出 1，精确提示 `3.12.12 not in '<3.12'`；见 `python312-resolver.log`。无获批 OCR fixture，不执行候选模型识别实验。

## 剩余门禁

Alpha、Beta、远端 CI/Artifact、Read the Docs、protected environment、正式发布后核验及独立 Review 均不得在缺少实测证据时标为通过。Beta 和 Stable 上传需维护者另行授权。

## B1–B3 实施记录

- B1：Requires-Python `>=3.11,<3.12`、Linux classifier；运行依赖四项 pin 原样保留。定向 metadata/API 测试 **4 passed**，`dist/p4/b1-junit.xml`。
- B2：内部候选 `0.3.0a1`，runtime 使用 SCM 生成版本并保留源码 fallback；同步 setup/docs/bumpversion/cookiecutter，关闭 bumpversion 自动 Git commit/tag。历史 README badge 仍指向实际已发布 v0.2.6。RTD Python 3.11；canonical RTD，Pages mirror；HTML/linkcheck 分离；补充 P0–P3 变更说明与发布维护手册。
- B2 定向 metadata/API/CLI **12 passed**，`b2-junit.xml`；Sphinx 7.2.6 使用 `sandbox-exec ... .tox/docs/bin/python -m sphinx -E -W -b html docs dist/p4/docs` 最终退出 0，`b2-docs.log`。初次严格构建发现两处新标题线长度错误及既有 Alabaster 不支持的 githuburl，均修正，未降低告警级别。
- 实际禁网 `tox -e check -v` 退出 0，`dist/p4/check.log`；pre-commit --all-files 只覆盖 tracked，新文件另跑 Ruff/Black，不冒称 untracked 已被该命令覆盖。
- B3：新增显式 MANIFEST、元数据/路径/秘密模式/白名单审计与 SHA256 manifest、独立安装 smoke runner 和 Dockerfile；构建后端 pin 到现有环境版本（setuptools 84.2.1 / SCM 10.3.4），frontend build 1.2.2.post1，运行依赖不变。
- 本地从最小源码导出目录 `dist/p4/source-b3` 禁网构建 sdist/wheel；首次导出没有 .git/生成版本/editable/build 遗留，但修复后曾复用该目录，最终无遗留构建另见下节。**不是已提交的干净 checkout**，最终 clean checkout/远端证据仍待人工交付。命令：`dist/p4/tools/bin/python -m build --no-isolation --sdist --wheel --outdir dist/p4/release-b3 dist/p4/source-b3`，外加系统禁网，退出 0。工具预装于独立 venv；版本见命令及后续证据。
- 首轮 Twine 严格检查因缺 `long_description_content_type` 失败；sdist 审计发现 global-exclude 误裁必要 egg-info。已补 RST 内容类型与必要生成 metadata，再构建新目录（保留原失败产物），Twine strict 两包 PASS；内容审计与 `--verify` PASS。
- B3 当时新增 metadata/artifact 合成单元测试 **21 passed**，`b3-unit-junit.xml`；包括污染文件、路径穿越、敏感模式、版本/依赖/Python/entry-point 漂移、缺模块、sdist symlink 和 manifest 防篡改。真实安装测试另记，不以合成 archive 测试代替。

## B3 双安装与最终产物

- 初轮两种产物在两个全新 Linux venv 安装成功；系统 NetworkMode=none、OS 探针、实际 import（没有 Mock OCR）、runtime/distribution/expected version、九项旧 API 精确签名/绑定/导出顺序、错误类导入、TradingClient 合成凭证构造/close、`emt --help`、`python -m emtl --help`、两次 pip check 全部通过。`package-installed-smoke.log` 记录两次 PASS 及完整依赖清单，容器 inspect 为 `package-container-inspect.json`。
- 自检注意到中间修复后重用了初轮 source-b3 目录，故不把该中间重建冒称“无构建遗留的最终构建”。另从当前文件重新创建完全空白的 `dist/p4/source-package-final`，构建前确认不存在 .git/build/dist/egg-info/生成版本；记录 `final-package-source-sha256.json`。
- 最终命令：系统禁网下 `dist/p4/tools/bin/python -m build --no-isolation --sdist --wheel --outdir dist/p4/release-final dist/p4/source-package-final`，退出 0；Twine 6.1.0 strict 和真实 archive 审计均 PASS。原始日志 `final-package-build.log`、`final-twine.log`；最终文件/版本/依赖/哈希清单 `release-final/manifest.json` 和 `SHA256SUMS`。不宣称两次构建的压缩包字节完全确定性一致。
- 最终产物已在另一个全新 Linux `NetworkMode=none` 容器重新双安装，分别位于 `/venvs/wheel` 和 `/venvs/sdist`；容器退出 0、两个实际 smoke PASS、两个 pip check 通过。原始日志 `final-package-installed-smoke.log`、`final-package-container-inspect.json`；汇总 `final-evidence-summary.json`，未把初轮不同 SHA 的通过结果套到最终包。
- 最终 wheel SHA256：`0c0a1b3ebe60542f5a6e421fc79da1de37c0bc8c7350d9811c530ab6fb092cef`；sdist SHA256：`463887f11a742a182e9bfe03b56a9aa82b6813b051b289c2d0f64859cb78d723`。双安装后再次 `audit_packages.py --verify` 通过，原始包未改变。
- 最终严格 HTML 构建前，将该 wheel 离线安装到已有文档依赖环境，避免沿用旧 editable distribution 的版本；HTML 实测版本为 `0.3.0a1`，canonical 指向 RTD。未把仅语法构建成功冒充候选版本一致性。

## B4 / S7 / S8 实施与风险检查

- 新增 Package Alpha workflow：PR/master 只构建/审计/安装/禁网 smoke，保留日志、工具版本、SHA256；无发布权限。
- release.yml：v* tag 只验证；上传必须从 master 显式 workflow_dispatch + publish=true + beta/stable 匹配，并经 pypi 环境审批。git tag/HEAD、master ancestry、干净工作区、candidate/Changelog、同 SHA master push 的 Build/check/docs/coverage/finish 和 Offline job 均需通过；PR、旧成功掩盖新失败、skip、缺证据都拒绝。
- 构建一次，同一命名 immutable Artifact 供 smoke 和 Publish 下载；manifest 与 SHA256SUMS 均复核，发布目录只复制已验证的两个包，不重建、不 skip-existing。OIDC 仅 Publish job；PyPA action 固定到只读核实的完整 commit SHA。
- 自检发现 manual dispatch 的 GitHub 事件 SHA 与 tag checkout SHA 可能不同，新增强制相等及两项失败/成功测试，防止 provenance 指向错误提交。master 已推进但 tag 较旧时，不得用较新事件 SHA 冒充该候选；见发布手册停止条件。
- 2026-11-09 收尾加固：不得执行候选 tag 自带的门禁来证明自身已合并。release/mirror 改为先从可信 master/工作流事件提交复制校验器到 RUNNER_TEMP，再 checkout 候选，使用 `python -I` 执行可信副本；候选依赖安装延后到 ancestry/CI 门禁通过之后。Publish 也使用可信校验/审计副本。两项新增 workflow 结构回归验证顺序和隔离路径；修正了旧静态测试未锚定行首、误把 input.publish 当 job.publish 的分段方法。该批定向最终 46 passed，原失败日志不冒称通过。另在仓库外复制件放入合成 packaging/validator 毒化模块，实际执行隔离校验器 help 与最终包审计均通过，未执行候选影子模块；见 `trusted-validator-isolation.json`。
- GitHub Pages 保留为独立手动 stable-only mirror；先核对发布版本存在及同 SHA CI，不接受 Alpha/Beta。RTD 为唯一 canonical，HTML-only；未修改远端 RTD/Pages 设置。
- SECURITY.md 提供公开 author email 的私密初始联系路径，不索要秘密；GitHub Private Vulnerability Reporting 实测 disabled，未擅自启用。Dependabot 每月检查 root/ci/docs pip 与 Actions，仅开 PR；维护者负责审查，不引入自动合并。
- [依赖审查](P4-dependency-review.md)：requests 2.31.0 / cryptography 42.0.5 命中公开公告，含凭证、OpenSSL 和证书验证风险。未证明 emtl 实际可利用，也未完成适用性/升级/延期决定，**阻断公开 Beta/Stable**；不擅自升级运行时依赖。
- [桌面推演](P4-release-drill.md) 覆盖构建失败、污染/漂移、上传不确定、已发布风险、无安全旧版本回退及 docs mirror 失败。没有执行真正上传、yank、订单补偿或真实账户操作。

## 最终测试与原始证据

所有命令 cwd 为 `/Users/lld/emtl`；本机测试统一在 `sandbox-exec -p '(version 1)(allow default)(deny network*)'` 下执行；Linux 测试容器创建即 NetworkMode=none，未注入宿主账户凭证。

| 检查 | 实测结果 | 原始位置（`dist/p4/` 下） |
| --- | --- | --- |
| 改动前完整基线 | 467 passed | baseline-junit.xml |
| 最终 macOS 真实 tox / 完整 suite | 545 passed，0 failure/error/skip（2026-11-09 可信校验器加固后） | final-r2-local-tox.log、final-r2-tox-result.json、final-r2-local-junit.xml |
| Linux 真实 tox 默认入口 | 545 passed，容器退出 0 | linux-final-r2-reports/junit.xml、tox-result.json、command-02.log |
| Linux 仓库外、不同顺序 | 545 passed，同节点集 | linux-final-r2-reports/outside-junit.xml、command-03.log |
| Linux 显式 tests/ | 545 passed，同节点集 | linux-final-r2-reports/explicit-junit.xml、command-04.log |
| OS 网络探针 / tox 父环境隔离 | 通过；NetworkMode=none；account environment isolated | linux-final-r2-container-inspect.json、linux-final-r2-reports/command-00.log、command-02.log、synthetic-environment.json |
| 原 467 节点 / 旧文件保持 | 全部保留；37 个原生产/测试/guard/Offline 文件字节不变 | final-r2-verification-summary.json、preserved-p0-p3-files.json |
| 最终包独立安装 / API/CLI / 构造 / pip check | wheel 与 sdist 均 PASS；NetworkMode=none，容器退出 0 | final-package-installed-smoke.log、final-package-container-inspect.json、final-evidence-summary.json |
| 当前实现对应受测快照 | 67 个源码/测试/CI/config 文件 SHA256 相同；报告收尾不冒称镜像内完整文档树相同 | tested-r2-implementation-match.json、final-r2-source-sha256.json |
| tox check / tracked pre-commit | 退出 0 | final-r2-check.log |
| Ruff / Black（显式包含 untracked Python 文件） | 退出 0；42 文件 Black 通过 | 本次工具调用记录；不以 tracked-only pre-commit 替代 |
| 工作流 YAML / run-block Bash 语法、Dependabot YAML | 通过；只是语法/静态及离线合成门禁证据，不是 GitHub Actions 端到端通过 | workflow-syntax-final.log、workflow-syntax.log |
| Sphinx 7.2.6 strict HTML | 退出 0，系统禁网，未运行在线 linkcheck | final-r2-docs.log、docs-final/ |
| bumpversion Beta/rc/stable 配置 | bump2version 1.0.1 在仓库外临时复制件实际同步 0.3.0b1 / 0.3.0rc1 / 0.3.0；--no-commit --no-tag；没有项目 Git 操作 | bumpversion-check.json |

Linux 版本：CPython 3.11.18、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2、tox 4.67.13；macOS CPython 3.11.14 / tox 4.67.12。覆盖率口径未改，含当前生成版本文件，不直接拿与 P3 的总行数差异宣称质量提升。

最终 macOS 命令（外加上述系统禁网前缀、`PIP_NO_INDEX=1` 和已安装的 Python 3.11 TOXPYTHON）：

```bash
.venv/bin/python -m tox -e py311-cover -v --result-json dist/p4/final-r2-tox-result.json -- python -m pytest -p no:cacheprovider -q --junitxml=dist/p4/final-r2-local-junit.xml --cov --cov-report=xml:dist/p4/final-r2-local-coverage.xml --cov-report=json:dist/p4/final-r2-local-coverage.json
```

Linux 实际执行既有 `ci/run_offline_tests.py`；其每个命令/cwd/退出码在 `linux-final-r2-reports/commands.json`，没有削弱三入口或 credential/OS guard。较早 498/541/543 项记录是当时批次，不代替本节最终 545 项。第一次本地 tox 因后端 pin 变化重建 .pkg 后缺离线 SCM wheel 而失败；独立用 uv 预装工具后，再禁网真实重跑通过。失败不记为测试通过。

## 偏差、修改清单与验收边界

1. **本地 Docker 环境偏差：** 完整 package image 构建的依赖安装已完成，但本机分层导出长时间未完成、CLI 超时；没有称镜像整体构建成功。为避免重复联网下载，使用已准备 wheelhouse 的 COPY stage，在全新 NetworkMode=none 容器内分别新建 venv、安装两个产物并运行当前 smoke；比允许网络的准备阶段更严格，但不等于实际 CI 完整镜像构建已验收。Linux 全套也从干净源码导出 + 缓存公开 wheel，在新禁网容器预装后执行原驱动。完整默认 Dockerfile/新增 workflow 端到端仍须最终远端 CI 证据。
2. **流程偏差：** 用户禁止自动 Git commit，故未按“每批独立 commit”创建提交；每批测试和历史失败保留。本地先准备 S7/S8 独立维护配置，不执行未获授权的 B5/B6；Beta/Stable 的发布、观察与退出仍未完成。无 fixture，不执行候选 OCR 引擎安装/识别实验，不把 metadata 调查冒充 K2 通过。
3. **交付范围：** 交易源文件 client/core/protocol/errors/coordination/CLI/const/utils 和原测试、guard、Offline workflow/驱动均未修改。唯一包源码变化是 `src/emtl/__init__.py` 的版本读取。

| 文件 | 修改用途 |
| --- | --- |
| setup.py、pyproject.toml、MANIFEST.in | 安装范围/平台声明、候选 fallback、RST metadata、后端 pin 与交付白名单 |
| src/emtl/__init__.py、.bumpversion.cfg、.cookiecutterrc | SCM runtime 版本、候选同步、关闭自动 Git 操作 |
| ci/requirements.txt、ci/offline.Dockerfile、tox.ini | frontend、测试工具依赖/必要配置复制、HTML/linkcheck 分离；原离线保护保留 |
| ci/audit_packages.py、ci/package_smoke.py、ci/package-smoke.Dockerfile、ci/run_package_smoke.py | 内容/版本/哈希、独立安装与 API/CLI/构造 smoke、禁网与失败证据 |
| ci/release_gate.py、.github/workflows/release.yml、.github/workflows/packages.yml、.github/workflows/document.yml | exact-SHA/审批/权限/Artifact 门禁、内部 Alpha、稳定版 mirror |
| tests/test_package_metadata.py、tests/test_package_artifacts.py、tests/test_package_ci.py、tests/test_release_gate.py | 新增 78 个离线用例；不改旧断言 |
| README.rst、CHANGELOG.rst、CONTRIBUTING.rst、.readthedocs.yml、docs/conf.py、docs/index.rst、docs/installation.rst、docs/reference/emtl.rst、docs/releasing.rst | 准确支持范围、变更/兼容/反馈/回滚/维护、canonical 与 HTML-only |
| SECURITY.md、.github/dependabot.yml | 私密报告与轻量依赖审查 |
| docs/refactor/plans/P4-plan.md、docs/refactor/reports/P4-acceptance.md、docs/refactor/reports/P4-dependency-review.md、docs/refactor/reports/P4-release-drill.md | 批准、实施细化、验收、依赖风险、无发布桌面推演 |

**尚不满足 P4 PASS 的事项：**

- GitHub pypi environment required reviewers 未配置（实测 protection_rules=[]）；Private Vulnerability Reporting 未启用，邮件仅为公开 metadata 已有联系地址，投递/响应未验证。
- requests/cryptography 命中公告，尚无维护者逐项适用性评估和修补/延期批准。
- 最终干净 checkout/PR head 的 Build、Offline、Package Alpha、Artifact/Tree 对应，以及 RTD 构建、Pages mirror 的远端证据未取得。未运行线上 linkcheck，不虚称所有外链可用。
- Beta 未上传、未观察/分类外部反馈、未批准退出；Stable 及发布后 PyPI 文件/provenance/正式包源安装均未执行。
- 独立 Session Review 未执行；本次 tracked/untracked 自检不是独立 Review PASS。

本地证据均在被 Git ignore 的 `dist/p4/`，未上传 Artifact；应由维护者保留，交付后用最终 SHA 远端证据固化。截至本地 Build 收尾，没有 Git commit、push、tag、GitHub Release、PyPI 上传、远端配置变更或真实账户/券商调用；后续 Git 交付授权另记如下。

2026-11-09 最终自检：tracked/staged/untracked 均检查；无 staged 变更，HEAD 仍为开始提交。`git diff --check` 与 `git diff --cached --check` 通过；当前实现仍与最终 R2 受测快照一致。最终汇总及原始证据 SHA256 索引分别为 `dist/p4/final-evidence-summary.json`、`final-evidence-sha256.json`。已导出报告后仅清理本次创建的已停止测试容器；未清理其他工作、镜像或证据。结论仍为 **NEEDS EVIDENCE，不能宣布 P4 PASS 或公开发布就绪**。

## 后续 Git 交付授权（2026-11-09）

维护者在 Build 交付后明确授权：仅 commit + push 当前 `refactor/p4-release-maintenance` 分支，暂不 tag、上传或发布。不创建 PR、不合并、不触发手动发布、不修改远端权限。远端分支提交前核实仍为开始 HEAD；67 个实现/测试/CI/config 文件与 R2 受测快照相同。提交前再次完整执行 macOS 系统禁网 pytest：545 passed，0 failure/error/skip，结果存于 `dist/p4/precommit-junit.xml`、`precommit-tests.log`。

此前按批实施但依授权未自动提交，本轮以一个完整受测快照交付（不伪造逐批历史）；最终提交与推送状态以实际 Git 输出和远端 ref 核验为准。本授权不解除依赖公告、审批保护、独立 Review、最终 SHA 远端 CI 或 Beta/Stable 的阻断项。

提交前所有 36 个交付文件加入暂存后，使用既有 Python 3.11 tox check 环境禁网检查：metadata check 及 ruff/black/whitespace/EOF/debug hooks 全部通过，未改动暂存内容，日志 `dist/p4/precommit-check.log`。直接调用 pre-commit 时曾选择缺构建依赖的新 hook 环境而失败；该环境准备失败不记为通过，后续实际完整 tox check 通过才继续提交。

## PR #10 Package Alpha 构建审计失败与修复待验（2026-11-09）

- 历史失败：PR #10，受测 head `1ff2eee9901e38c357961e07c429266087e2bc79`，Run [42547411046](https://github.com/riiy/emtl/actions/runs/42547411046)，Job [128935288776](https://github.com/riiy/emtl/actions/runs/42547411046/job/128935288776)。`Build internal candidate once` 退出 1；后续 `Install and smoke the same artifacts without network`、`Recheck unchanged artifacts` 未执行，不得冒称远端 smoke PASS。
- 原日志记录 `Successfully built emtl-0.3.0a1.tar.gz and emtl-0.3.0a1-py3-none-any.whl`；Twine strict 两包均 PASSED；`ci/audit_packages.py:83` 抛出 `ValueError("non-delivery file in artifact")`。
- 同一构建日志确认 setuptools 84.2.1 把 `AUTHORS.rst` 作为合法作者/许可证文件放在 sdist 根目录、wheel 的 `emtl-0.3.0a1.dist-info/licenses/AUTHORS.rst`。当前审计白名单分别遗漏 `ROOT_FILES` 中的 `AUTHORS.rst`、`DIST_FILES` 中的 `licenses/AUTHORS.rst`。
- 定向修复范围：只允许这两个**精确路径**；将合成 wheel/sdist fixture 与当前实际生成布局对齐，并保留/补充对未经批准的 license 文件、测试文件、CI 临时文件、私钥、敏感路径、路径穿越及符号链接的拒绝测试。`MANIFEST.in`、生产交易代码、依赖及 Release 发布权限不变。
- 初次失败 Run 上传了名为 `alpha-package-evidence` 的 Artifact（ID `13643962489`），但这是失败构建的部分证据，不能作为完整审计、安装 smoke 或发布验收的 PASS 证据。
- **证据边界：** 此条作为 GitHub 定向补丁的待验记录，不代表已运行最终干净 checkout 的 sdist/wheel、Twine、真实包审计、禁网双安装、完整 pytest、pre-commit 或新的远端 CI。修复应用后必须记录每项真实命令/退出码、更新后的 PR head SHA、新 Run/Artifact 和独立 Review；在取得证据前，P4 仍为 **NEEDS EVIDENCE**，Beta/Stable 仍 **BLOCKED**。

## 2026-11-09 requests 安全修复与 PyPI required reviewers 边界

- 将 `requests==2.31.0` 命中公告作为阻断项；建议候选 `requests==2.33.1`，同步严格包元数据与 Requests Session 定向回归；详细公告及真实调用路径见 `P4-dependency-review.md` 的 requests 专项。
- 此处记录安全修复的实施意图，**不能作为实际 CI 已通过或公开发布已完成的证据**。必须用最终 PR Head 和最终 master push 的 Build/Offline/Package Alpha 三项工作流结果及 Artifact 替换待验状态。
- PyPI 发布工作流已有 `environment: pypi` 和 `id-token: write` 仅 Publish Job 的配置，但是否真正设置 `Required reviewers` 是 GitHub 远端 Environment protection rule，不能通过仓库代码提交代替。
- 2026-11-08 的实测 `pypi.protection_rules=[]` 是历史证据。当前 GitHub 集成不提供环境规则写入及完整环境设置读取权限；因此**不能声称 required reviewers 已配置**。需管理员打开 `https://github.com/riiy/emtl/settings/environments`，进入 `pypi` → 勾选 Required reviewers → 选择有仓库读取权限的审核人 → Save protection rules；按维护团队情况考虑 Prevent self-review 与禁止绕过规则。
- 配置完成后，使用有足够权限的本地 `gh api repos/riiy/emtl/environments/pypi --jq '.protection_rules'` 确认存在类型为 `required_reviewers` 且 reviewer 非空的规则；不能通过创建 tag 或上传 PyPI 来试探安全设置。进一步审批行为实测须单独安排非发布场景，防止误触发真实 Publish。
- 除非得到 Environment rule 真实证据及独立 Review，P4 仍 **NEEDS EVIDENCE**，公开 Beta/Stable 仍 **BLOCKED**。


## 2026-11-09 最终 master 收尾证据（覆盖早期待验状态）

### 受测提交与远端 CI

- master commit：`624fc5aba6875b89202d16b5db9d6c927c48fb8b`
- master tree：`db8b5ae9b35763dc2bedfb4b405f8c59a1524647`
- 三个 Run 均为 `push` 事件、`master` 分支、相同 head SHA，且 Run 与所有 Job 均 success：
  - [Build](https://github.com/riiy/emtl/actions/runs/42585602357)：`check`、`docs`、`py311-cover (ubuntu)`、`finish` 全部成功。
  - [Offline tests](https://github.com/riiy/emtl/actions/runs/42585602255)：`offline` 成功；Artifact `offline-test-evidence` ID `13659326002`。
  - [Package Alpha](https://github.com/riiy/emtl/actions/runs/42585602194)：`package` 成功；Artifact `alpha-package-evidence` ID `13659046312`。

### Artifact 原件核验

- Offline Artifact ZIP SHA256：`d23bbd40ed2260012d33633a7f5478a8d3cf9b2db8c29b0a729b4e297c4f5af7`。
- Offline 镜像：`sha256:6df9178706ed3999b36098cfe9f092fc0c3beef2d0d8ecd2d2ac92b58beda2df`；`NetworkMode=none`；容器退出码 0；宿主证据收集/清理退出状态均为 0。
- 三份 JUnit（默认入口、仓库外入口、显式 `tests/`）分别 559 passed、0 failure、0 error、0 skipped，节点数和集合一致。
- Coverage：行覆盖 95.97%（468/482）；分支覆盖 91.23%（104/114）。此数字只记录该 Artifact 的 coverage.json，不与 P3 旧口径直接比较。
- Package Alpha Artifact ZIP SHA256：`658f8fbb7c4e04793eca0ee1bca3b487fa4504ca8fb657988a3bf66a61852b1c`；Artifact 的 `release/commit.txt` 与上述 master SHA 一致。
- Package smoke 镜像：`sha256:5c8aa9e3f9cfc2b834984cfa03c5cb6bd99908624a9631bcb42fdd379b12a255`；容器 `NetworkMode=none`，退出码 0；wheel 和 sdist 分别在独立环境安装、smoke、`pip check` 均成功。
- Wheel SHA256：`183495fb00f233f79ff0bae84b5934bf69cde2c057dc4fa7312b599c1fe8a935`。
- sdist SHA256：`06e18561c8826022436de6fb25fd1340c6f25c7ff36252ed5c7144d2c34dd9af`。
- Artifact manifest 确认版本 `0.3.0a1`、Requires-Python `>=3.11,<3.12`、直接依赖 `rsa==4.9`、`requests==2.33.1`、`ddddocr==1.4.11`、`cryptography==50.0.2`；`SHA256SUMS` 对两种产物复核均 OK。

### PyPI Environment 静态保护

维护者提供的当前 `gh api repos/riiy/emtl/environments/pypi` 输出包含：
- `required_reviewers`：审核人 `riiy`，`prevent_self_review=false`。
- `custom_branch_policies=true`，`protected_branches=false`；分支策略列表仅有 `master`。

这确认了静态配置。单人维护时允许 self-review 可避免唯一审核人无法批准自己触发的部署，但不提供第二人独立复核。不得把静态配置当成审批实际运行证据。

本分支新增 `.github/workflows/pypi-approval-probe.yml`：仅 `workflow_dispatch`，需显式将 `run_probe=true`；job 绑定 `pypi` Environment，`permissions: {}`，不 checkout、不配置 OIDC、不构建、不调用 PyPI、不上传。合并后由维护者从 `master` 手动触发，先确认 Job 显示 Waiting for approval，再批准并确认 Job 成功及日志明确无上传。当前 GitHub 连接不提供 workflow dispatch / deployment approval 动作；这一步仍需维护者在网页完成。

### 文档与 Read the Docs

- 维护者已在此前会话确认：tox docs、Sphinx HTML、autodoc、中文导航及 Read the Docs 远端 HTML 构建验收通过；PDF/EPUB 不再生成。
- 本轮未取得对应 RTD Build ID 或 API 原始结果，故标记为 **维护者确认 PASS，独立远端记录 NEEDS EVIDENCE**。不得将历史失败 Build 35727016 当作最终结果，也不得凭本地 Sphinx 构建代替 RTD 远端证据。

### 当前结论与未授权范围

- P4 实现和最终 master 的 Build / Offline / Package Alpha / 包安装证据：PASS。
- 已知 requests 2.31.0、cryptography 42.0.5 公告对应的升级和兼容性测试：见依赖审查报告 2026-11-09 更新；不宣称完成全量 SBOM 或未来零漏洞保证。
- Required reviewers 静态配置：维护者提供证据，PASS；审批行为：等待 no-upload probe。
- **P4 总体仍 NEEDS EVIDENCE**，直到 no-upload 审批探针和 RTD 远端 build 记录核验完成。Beta 的十个工作日反馈窗口、退出决策及 Stable 另行批准仍未执行；不得据此宣布已发布或对真实券商生产可用。
- 本次不创建 tag、GitHub Release，不上传 PyPI，不执行真实账户或交易操作。


## 2026-11-09 PR #23 合并后最终 master 验证

### 合并与代码树对应

- PR：[ #23 P4 closeout: exact-SHA Alpha gate and safe PyPI approval probe ](https://github.com/riiy/emtl/pull/23)
- PR head：`66d3a3b58b55ba047bef595f497874c7fd619c88`
- Merge commit / master：`d5eb7d71e4b65fb28e0398b64269a9d1225c833a`
- PR head 与 merge commit tree 均为：`f9d361cec8d5a23e2f3b6576efbc63d915250633`；文件树完全一致。

### 最终 master push CI（精确匹配 merge SHA）

- [Build](https://github.com/riiy/emtl/actions/runs/42622822695)：success；`check`、`docs`、`py311-cover (ubuntu)`、`finish` 全部成功。
- [Offline tests](https://github.com/riiy/emtl/actions/runs/42622822706)：success；Artifact ID `13676768110`。
- [Package Alpha](https://github.com/riiy/emtl/actions/runs/42622822718)：success；Artifact ID `13675948724`。
- 三个 Run 均为 `push` / `master`，head SHA 都是 `d5eb7d71e4b65fb28e0398b64269a9d1225c833a`。

### 最终 master Artifact 原件

- Offline ZIP SHA256：`3c964e0c18ff3026948ee37921bdc2965e6fb1ecac798de322d5b31ccd290b73`。
- Offline Linux image：`sha256:037cc5c84a23ae02e7f71ad547a05551d16b9d32edb025ffd2360a1eb75d63b8`；`NetworkMode=none`；容器退出 0。
- 默认入口、仓库外入口、显式 `tests/` 三份 JUnit 各 **565 passed**，0 failure、0 error、0 skipped；节点集一致。
- Coverage：行 95.97%（468/482），分支 91.23%（104/114）。
- Package Alpha ZIP SHA256：`4394938d4dcaa86e68001dd7206d9857d4c555d4dabc40aedfe754e00aff457d`；Artifact 内 `release/commit.txt` 精确等于 merge SHA。
- Package smoke image：`sha256:aa40f38017468aeeed402a69c985c22bb75ea581e125773017a788038c3a0945`；`NetworkMode=none`；容器退出 0；wheel/sdist 独立安装与 smoke 成功，`pip check` 成功。
- Wheel SHA256：`1de67b7c41772d70972c9e60b114ec9031088032aed0b18505dc0e6ac7bc44a6`。
- sdist SHA256：`b4bb90f049aaf6b9fb2bfd81ff8b3848a28d12941680a9fe9e74494610e2c567`。

### PR #23 改动复核与剩余步骤

- Release Gate 已把 `packages.yml: package` 纳入必需 exact-SHA master push 工作流集合；新增合成测试拒绝 Package Alpha 缺失、失败、skipped 或 head SHA 不匹配。
- `.github/workflows/pypi-approval-probe.yml` 已合并。该工作流只需人工 `workflow_dispatch`，绑定 `pypi` Environment，`permissions: {}`，无 OIDC、无 checkout、无构建、无 PyPI token、无上传步骤。
- 维护者仍需从 master 手动运行该 probe，记录 Job 先进入 Waiting for approval、指定 reviewer 批准后 Job 成功。GitHub 连接未提供 dispatch/approval 动作，本轮没有替维护者触发。
- RTD 远端 HTML build：维护者已确认验收通过；本轮未取得 Build ID，保留为“维护者确认 PASS、独立记录未核验”。
- **P4 总体仍 NEEDS EVIDENCE**：审批行为验证和 Beta 反馈窗口/退出决策未完成。Stable 发布仍需单独授权。本轮没有创建 tag、GitHub Release 或上传 PyPI。
