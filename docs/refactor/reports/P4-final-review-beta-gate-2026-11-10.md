# P4 最终独立 Review 交接与 Beta 准入决定（2026-11-10）

> 本文件是当前会话执行的**只读证据预审和独立 Review 交接清单**，不是独立 Reviewer 的签字结果，也不是 Beta/Stable 的发布授权。不得在本文件基础上自动创建 tag、Release 或上传 PyPI。

## 1. 适用基线与决定

- 受审主线：`master` SHA `1f9746c1a892a11e3506fe4c6165f269f6dccd6d`（PR #29 合并）。
- **工程准备证据：PASS**。主线 Build、Offline、Package Alpha 及 RTD 中文 HTML 构建成功；当前只读重新核对源代码、Workflow、原始 Artifact 和 SHA256。
- **独立最终 Review：NEEDS EVIDENCE**。截至本次查询，PR #22–#29 的 GitHub Reviews API 均返回空列表；没有可归属独立 Reviewer 的完整审查、结论和签字。P4 要求使用独立 Session，当前会话预审不能冒充这一过程。
- **当前 Beta 上传决策：NO-GO（暂缓）**。允许准备 `0.3.0b1` 候选 PR；但独立 Review、Beta 版本/变更记录同步、精确 SHA 主线重新验收以及维护者明确授权尚未完成。未创建或上传任何 Beta。
- **P4 整体：NEEDS EVIDENCE**。即使后续 Beta 上传成功，仍需十个工作日左右的反馈窗口、问题处理和独立的 Stable 批准，不能提前标 PASS。

## 2. 最终 master 的原始证据（同一 SHA）

| 项目 | 已核实证据 |
| --- | --- |
| Build | [Run #42788468361](https://github.com/riiy/emtl/actions/runs/42788468361)，`check`、`docs`、`py311-cover (ubuntu)`、`finish` 全部 success |
| Offline | [Run #42788468308](https://github.com/riiy/emtl/actions/runs/42788468308)，`offline` success，Artifact `13750805706` |
| Package Alpha | [Run #42788468365](https://github.com/riiy/emtl/actions/runs/42788468365)，`package` success，Artifact `13750875744` |
| 中文文档 | [RTD Build #35779520](https://app.readthedocs.org/projects/emtl/builds/35779520/)，正确 master SHA，Sphinx HTML `build succeeded.`，零 Sphinx 警告，中文索引成功；维护者确认线上访问恢复 |
| PyPI 审批探针 | [Run #42780759403](https://github.com/riiy/emtl/actions/runs/42780759403)，先前 master 基线上 `pypi` Environment 真实 approval 及无上传 job 成功；仅证明当次门禁，不证明真实 PyPI publish 或第二人审查 |
| GitHub Releases | 当前 REST `releases` 列表为空；未见新版本 GitHub Release |
| 当前公开版本 | [PyPI emtl](https://pypi.org/project/emtl/) 显示最新 `0.2.6`，还没有 `0.3.0b1` |

### 下载原始 Artifact 后的复算

- Offline Artifact ZIP SHA256：`773c96795e310b7c7628c2c456455b6ebdfd57864f7d26db758f212958e7139d`，与 GitHub 提供的 `digest` 相同。
- Package Artifact ZIP SHA256：`9082e4974e0b7b8e27cae2b6c1ecacae951379b58e26762f148a0ca09f985dc7`，与 GitHub 提供的 `digest` 相同。
- Offline 内的 `junit.xml`、`outside-junit.xml`、`explicit-junit.xml` 各 **565 tests、0 failures、0 errors、0 skipped**，三个测试节点集合完全相同。
- Offline 记录：`NetworkMode=none`，容器退出码 `0`，Python `3.11.18`。该 Artifact 的行覆盖率 `95.97%`，分支覆盖率 `91.23%`。
- Package Artifact 的 `release/commit.txt` 等于精确主线 SHA；`manifest.json` 记录内部 Alpha `0.3.0a1`、`Requires-Python >=3.11,<3.12`，依赖固定 `rsa==4.9`、`requests==2.33.1`、`ddddocr==1.4.11`、`cryptography==50.0.2`。
- Wheel SHA256：`15ddd5921ed41d46e2a2fbfb1031a4b3df11dd7e7be1fb8b3448bb26d33885c0`；sdist SHA256：`96377cf12062215d42e83460640ca6c0dfc68155e0ef29564e13eedb872ba6d6`。逐一复算与 Manifest、`SHA256SUMS` 相同。
- 包禁网 smoke 记录 `network-mode=none`、退出 `0`；sdist/wheel 独立安装、版本与 CLI/API/构造 smoke、`pip check` 已成功。这里仍是合成/禁网证据，不能证明真实券商侧响应和成交。

## 3. 源码与发布权限预审

- 重点核对 `.github/workflows/release.yml`、`packages.yml`、`pypi-approval-probe.yml`、`document.yml`、`ci/release_gate.py`、`ci/audit_packages.py`、`tests/test_release_gate.py`、`setup.py` 与 P0/P2/P3 契约。
- 发布工作流中 Tag 推送仅进入验证；Publish job 限制为 `workflow_dispatch`、从 `master` 手动执行且 `publish=true`。仅 Publish job 有 `id-token: write`，使用受保护的 `pypi` Environment 和 pin 到 SHA 的 PyPA action。上传使用 smoke 审计过的相同 Artifact。
- 门禁验证版本/tag、候选 SHA 为 master 祖先、无工作区脏文件、candidate/Changelog 一致、同 SHA `push/master` 的三个 Workflow 与必需 Job 成功；手动 Publish 还要求事件 SHA 等于目标 Tag SHA，并检查 Environment 存在有效 `required_reviewers`。
- `pypi` 历史静态配置允许 `riiy` 审批且 `prevent_self_review=false`；审批探针确实成功，但不能把单人自批解释成独立审查。实际上传时仍须再次检查实时规则。
- 当前 GitHub `master` Branch API 的 `protected=false`，仓库 Rulesets API 返回 `[]`。这表示合并前审查/CI 没有通过分支保护强制执行，是发布治理风险；推荐在 Beta 前启用适合当前维护团队的 PR/状态检查保护，不要在没有第二位 reviewer 的情况下配置导致自己无法合并的强制双人审批。
- 2026-11-09 依赖审查已对之前的 Requests、cryptography 命中公告采用定向修复并有最终主线 CI；**不是**全量 SBOM / 零漏洞保证。`rsa==4.9` 和 `ddddocr==1.4.11` 继续分别留给独立依赖审查/OCR 迁移，不能据此扩展 Python/OS 支持声明。
- 上述为只读配置与合成/运行日志检查；未实际触发 Release workflow 的 Publish，也未验证 PyPI OIDC 或 provenance 的真实发布端到端结果。

## 4. 指派给独立 Reviewer（新会话或与实施者独立的审查人）

请从**精确** master SHA 独立读取以下文件与证据，不将本报告结论当作事实证明：

1. `docs/refactor/requirements/P4.md`、`docs/refactor/plans/P4-plan.md`、`docs/refactor/reports/P4-acceptance.md`、`P4-dependency-review.md` 和 P0–P3 的契约、验收记录。
2. 比对 P4 初始实现至当前 master 的交易生产文件与 API/CLI；确认 P0–P3 行为及禁网/账号隔离/交易 Unknown 不重发契约没有削弱。
3. 独立检查 Release YAML 与 `ci/release_gate.py` 的发布触发、来源可信性、同 SHA CI、tag/版本、最小权限、Environment 审批和 Artifact 复用；尝试提出能绕过规则的最小反例。
4. 独立下载上述两个 Artifact，并重新核对 ZIP SHA256、内含 JUnit/coverage、NetworkMode/退出码、wheel/sdist Manifest、包元数据、依赖、禁网安装 smoke。
5. 阅读支持矩阵、已知漏洞定向修复及其不足、回退/Hotfix 流程、中文版文档；不要将历史 `0.2.6` 当作满足 P0–P3 的可信回退。
6. 核查 `master` 未保护与 `pypi` 自批的具体风险及部署前可接受的缓解手段。

请在**独立会话**形成明确审查结论 `PASS` / `FAIL` / `NEEDS EVIDENCE`，至少列出：Reviewer 身份或会话证据、精确 SHA、发现的问题及其严重程度、反例测试、证据 URL/哈希、阻断项与最终结论。独立 Review 不得由本预审或批准上传的维护者自批替代。

## 5. Beta GO / NO-GO 决策

### 当前：NO-GO 上传；GO 准备 Beta 候选

**在以下条件满足前，不允许 Tag 推送、GitHub Release 或 PyPI 上传：**

1. 独立 Reviewer 对上述代码/证据基线输出 `PASS`，重大问题已修复。若后续修改源码或发布配置，Reviewer 必须审查增量，而不能机械复用旧 SHA 结果。
2. 创建单独的 `0.3.0b1` 候选分支/PR；同步所有版本来源、测试期望、Changelog、README/安装/支持声明和 Beta 发布说明。保留 `0.3.0a1` 原始证据，不把 Alpha 包哈希冒充 Beta 包哈希。
3. Beta 候选合并后，在**最终 master SHA** 上重新获得 Build/Offline/Package Alpha 全部 success；独立核对新产物的原始 ZIP、sdist/wheel 哈希与禁网 smoke。
4. 核实最终 Tag `v0.3.0b1` 指向该精确 SHA；计划中的手动 Publish 必须来自 `master` 且事件 SHA 相同。若 master 已推进，停止并重做候选门禁，不以旧 Tag 拼接新 CI 证据。
5. 维护者**另行明确授权**创建 Tag、执行 `publish=true` 的 Beta Upload 与可选的 GitHub Pre-release；Publish 环境审批须再次明确。现有 Plan、这个报告及本 Draft PR 都**不**授权上传。

### 获批后的受控发布与退出

- Beta 为 PyPI 显式 opt-in：`python -m pip install --pre emtl==0.3.0b1`（只有实际上传后才有效）。声明 Linux / CPython 3.11，离线测试不证明真实券商协议，不要求用户提交秘密或真实交易记录。
- 发布后逐文件验证 PyPI 文件名、SHA256、provenance 的仓库/工作流/提交，并在干净 Linux/Python 3.11 环境从 PyPI 安装该精确版本、做无副作用 smoke。
- 建议观察约十个工作日，分类记录安装/环境、API/兼容、文档、缺陷、安全/交易风险反馈。出现泄漏、重复下单风险、账户串扰或不可解释的严重兼容故障立即停止推荐并处置；无反馈不当作交易安全证据。
- Beta 退出需所有阻断风险关闭或获明确延期披露，并由维护者另行批准 `0.3.0` Stable；此时才考虑 P4 最终 PASS，不能用 Beta 发布本身代替结束验收。

## 6. 停止条件

只做上述会影响 Beta 发布判断的最小工作。不再重复已通过的 Alpha 或 RTD 门禁；不扩大到 Python 3.12+/OCR 引擎迁移、真实交易测试、自动补单或新发布基础设施。若独立 Reviewer 未通过，归档问题并处理最小阻断项；不得降低门禁换取 `PASS`。
