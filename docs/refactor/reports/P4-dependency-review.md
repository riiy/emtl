# P4 依赖审查（2026-11-08）

> **当前版本状态（2026-11-09）：** 下文 2026-11-08 的公告命中表是旧 pin 的历史快照，不代表当前 master 仍在使用 requests 2.31.0 或 cryptography 42.0.5。PR #23 合并后的 master `d5eb7d71e4b65fb28e0398b64269a9d1225c833a` 已固定为 requests 2.33.1、cryptography 50.0.2；更新依据、兼容性测试和剩余限制见本文末尾。不要删除旧快照，它用于追溯升级前风险。


## 2026-11-08 历史结论（已由 2026-11-09 修复记录 supersede）

**历史状态：** 当时 requests 2.31.0 / cryptography 42.0.5 命中已知公告，公开 Beta / Stable 被阻断。当前 pin 与定向修复证据见本文末尾“2026-11-09 当前 master 依赖修复与剩余审查”；不得将此历史段落当作当前版本状态。

## 2026-11-08 历史清单与来源（升级前 pin）

| 类型 | 直接依赖 / 声明来源 | 策略与证据 |
| --- | --- | --- |
| 运行时 | setup.py：rsa 4.9、requests 2.31.0、ddddocr 1.4.11、cryptography 42.0.5 | 保持精确 pin；每次变更单独解释与回归，不整体升级 |
| 构建 | pyproject.toml：setuptools 84.2.1、setuptools_scm 10.3.4 | 复用现有已安装版本，固定后端；记录间接 packaging/vcs-versioning |
| CI / 前端 | ci/requirements.txt：virtualenv、pip、setuptools、six、tox、twine、build 1.2.2.post1 | 新增 frontend 固定版；其余沿用既有策略，每次归档实际工具版本 |
| 测试 / 检查 | tox.ini：pytest、pytest-cov、coverage、docutils、pre-commit、readme-renderer、pygments、isort、setuptools-scm | 保留既有工具/入口，不借此更新运行依赖 |
| 文档 | docs/requirements.txt：Sphinx 7.2.6 | 不升级；HTML 与在线 linkcheck 分离 |

本次 CPython 3.11 / Linux 全新 venv 的运行时解析结果：certifi 2026.10.23、cffi 2.1.1、charset-normalizer 3.5.2、cryptography 42.0.5、ddddocr 1.4.11、flatbuffers 25.12.19、idna 3.20、numpy 2.4.6、onnxruntime 1.31.1、opencv-python-headless 5.0.0.93、packaging 26.3、pillow 13.0.0、protobuf 7.36.2、pyasn1 0.6.5、pycparser 3.12、requests 2.31.0、rsa 4.9、urllib3 2.8.0。

完整安装日志 / freeze / 命令：`dist/p4/baseline/dependencies-{0,1,2}.log`、`dependency-commands.json`；属本机未上传证据，不是所有用户的锁文件或未来解析保证。安装产物 smoke 另输出实际环境清单。不是新增对这些传递版本的永久支持承诺。

## Python / OCR / 维护状态

- ddddocr 1.4.11 元数据 `<3.12`；真实 CPython 3.12.12 离线 resolver 拒绝，3.11 安装与 pip check 通过。
- 候选 ddddocr 1.6.1 的公开 metadata 为 `>=3.10`、MIT，依赖 numpy/onnxruntime/Pillow/平台 OpenCV。没有获批 OCR fixture，不运行识别对照、不更换模型、不宣称 3.12+ 兼容。
- CPython 3.10 已 EOL，不再作为声明范围；3.11 仍在安全维护期但有到期风险，维护者于 2027-04-01 前启动 OCR/Python 迁移复核。上游发布新版本不等于项目可无风险升级。

## 2026-11-08 已核实公开公告（旧 pin 命中快照）

只读调用 `POST https://api.osv.dev/v1/querybatch`，查询 PyPI 精确版本 requests 2.31.0、rsa 4.9、ddddocr 1.4.11、cryptography 42.0.5、urllib3 2.8.0；返回 HTTP 200。随后逐项读取下列 GHSA 的 OSV 记录，均 HTTP 200。PYSEC 别名不重复计数。

另单独读取 `PYSEC-2026-3554`（HTTP 200），确认它对应未在 querybatch GHSA 列表中出现的 `GHSA-m2h6-j472-rp4c`，不是重复项，补记如下。

| 包 | 公告 | OSV 摘要 / 首个修复版本 |
| --- | --- | --- |
| requests 2.31.0 | [GHSA-9hjg-9r4m-mvj7](https://osv.dev/vulnerability/GHSA-9hjg-9r4m-mvj7) / CVE-2024-47081 | 恶意 URL 导致 .netrc 凭证泄漏；2.32.4 |
| requests 2.31.0 | [GHSA-9wx4-h78v-vm56](https://osv.dev/vulnerability/GHSA-9wx4-h78v-vm56) / CVE-2024-35195 | Session 首次 verify=False 后的验证复用风险；2.32.0 |
| requests 2.31.0 | [GHSA-gc5v-m9x4-r6x2](https://osv.dev/vulnerability/GHSA-gc5v-m9x4-r6x2) / CVE-2026-25645 | extract_zipped_paths 临时文件不安全复用；2.33.0 |
| cryptography 42.0.5 | [GHSA-537c-gmf6-5ccf](https://osv.dev/vulnerability/GHSA-537c-gmf6-5ccf) | wheel 携带有漏洞 OpenSSL；48.0.1 |
| cryptography 42.0.5 | [GHSA-79v4-65xg-pq4g](https://osv.dev/vulnerability/GHSA-79v4-65xg-pq4g) / CVE-2024-12797 | wheel 携带有漏洞 OpenSSL；44.0.1 |
| cryptography 42.0.5 | [GHSA-h4gh-qq45-vh27](https://osv.dev/vulnerability/GHSA-h4gh-qq45-vh27) | wheel 携带有漏洞 OpenSSL；43.0.1 |
| cryptography 42.0.5 | [GHSA-jwv3-5hgf-82ww](https://osv.dev/vulnerability/GHSA-jwv3-5hgf-82ww) / CVE-2026-69249 | 重复自签中间证书导致指数路径构建；49.0.0 |
| cryptography 42.0.5 | [GHSA-m959-cc7f-wv43](https://osv.dev/vulnerability/GHSA-m959-cc7f-wv43) / CVE-2026-34073 | DNS name constraint 执行不完整；46.0.6 |
| cryptography 42.0.5 | [GHSA-r6ph-v2qm-q3c2](https://osv.dev/vulnerability/GHSA-r6ph-v2qm-q3c2) / CVE-2026-26007 | SECT 曲线缺少 subgroup validation；46.0.5 |
| cryptography 42.0.5 | [PYSEC-2026-3554](https://osv.dev/vulnerability/PYSEC-2026-3554) / GHSA-m2h6-j472-rp4c / CVE-2026-69248 | wildcard DNS 名可绕过 permittedSubtrees；49.0.0 |

OSV 对另外三项查询未返回公告，**不等于证明它们安全**；本次不是全量 SBOM 漏洞扫描。上述是版本命中，不是 emtl 调用路径的可利用性结论：需核查实际加密用法、wheel 内 OpenSSL、宿主 Session/netrc/CA 配置及不可信输入来源。默认测试禁网不能替代生产影响评估。

## 2026-11-08 当时拟定的下一步（已由后续记录 supersede）

由仓库维护者逐项决定定向修补或有依据的延期，记录适用性、版本范围、风险、验证及回退；HTTP 更新须保留请求次数、重定向、异常与零重发回归，密码学更新须验证既有加密契约。再跑完整 Offline、安装产物、兼容目标和文档构建。未经解释的高严重度问题不得进入公开 Beta；不得用自动升级或自动合并跳过审核。

## 2026-11-09 cryptography 安全修复专项（候选阶段历史记录）

> 本节记录合并前的候选状态；最终 pin、Artifact、远端 CI 和 RSA 兼容性结果以末尾“Requests / cryptography 修复最终记录”为准。

**历史状态：已完成风险及调用路径评估；当时仍待新 Head 的远端 CI 和独立 Review。** 之前列出的 `cryptography 42.0.5` 风险仍为历史有效记录；本节说明候选版本和风险处理，不追溯修改既有证据。

### 实际使用路径

- `src/emtl/utils.py::emt_trade_encrypt` 使用 `serialization.load_pem_public_key`、`rsa.RSAPublicKey.encrypt`、`padding.PKCS1v15` 对登录密码进行 RSA 公钥加密，然后做 Base64 编码。生产 PEM 公钥是固定内嵌值；未发现 emtl 调用 PKCS#7 解密、X.509 链验证、二进制曲线 ECDH/ECDSA 或载入任意第三方 RSA 公钥。
- 对 SECT subgroup、PKCS#7 解密 oracle、证书 name constraints 等已公布漏洞，现有调用链未见直接可利用路径，但无法把这解释为旧版 OpenSSL wheel 安全。42.0.5 仍落入多个已发布版本范围；特别是捆绑 OpenSSL 漏洞与项目实际 wheel 安装相关。
- 保持交易协议使用的 PKCS#1 v1.5 **加密**；不改为 OAEP。此次只是升级依赖，不修改生产实现/真实账户调用。

### 目标版本与依据

- 本次针对已开放的 Dependabot #18，采用 `cryptography==50.0.2`（2026-09-30）；官方 PyPI 元数据允许 Python 3.11，Linux wheel 的 OpenSSL 已更新到 4.0.3。
- 上游 GHSA-537c-gmf6-5ccf（CVE-2026-34180，旧 wheel 携带有漏洞 OpenSSL；48.0.1 修复），GHSA-r6ph-v2qm-q3c2（CVE-2026-26007；46.0.5 修复），GHSA-p423-j2cm-9vmq（CVE-2026-39892；46.0.7 修复），GHSA-jwv3-5hgf-82ww 与 GHSA-m2h6-j472-rp4c（49.0.0 修复）均早于目标版本得到修复。
- GHSA-g6cj-pr64-35w5（CVE-2026-69247）始于 44.0.0 且 50.0.0 修复；42.0.5 不在其影响范围内，不能误算为旧版本本来就受该公告影响。50.0.2 包含此修复。
- cryptography 49+ 的兼容性变化包括移除 macOS x86_64 wheel 和部分旧算法；emtl 已批准平台为 CPython 3.11/Linux，仍需对真实 RSA 加密路径和所有 Linux CI 实测，不因 PyPI metadata 就直接宣布兼容。

来源：
- https://github.com/pyca/cryptography/security/advisories
- https://github.com/pyca/cryptography/security/advisories/GHSA-537c-gmf6-5ccf
- https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5
- https://cryptography.io/en/50.0.2/changelog/
- https://pypi.org/project/cryptography/50.0.2/

### 修复与验收

1. 仅同步 `setup.py` 的 pin、`ci/audit_packages.py` 的严格依赖元数据契约、相关合成包测试和 `tests/test_package_metadata.py`。不扩大依赖允许集合，不放宽文件或秘密扫描。
2. 新增 `tests/test_cryptography_compat.py`：确认安装版本；真实载入现有生产公钥、PKCS#1 v1.5 密文长度和 Base64；用临时合成 2048 位 RSA 密钥对完成 UTF-8 加密/解密回环。无真实凭证、无 HTTP/券商访问、密钥不写盘。
3. 在新 PR Head 实测：Build (包括 docs/check/py311-cover)、Offline tests（OS NetworkMode=none，三入口）、Package Alpha（sdist/wheel 审计、Twine strict、禁网双安装 smoke），三项均通过且 SHA 匹配才可合并。
4. 合并后重新核验最终 master 的 Build、Offline tests、Package Alpha；不以旧版/PR Head 成功代替合并后的证据。
5. 如发生 RSA PEM 解码、加密输出、依赖解析或远端 CI 回归，维持阻断并停止合并，不删除测试或回退审计严格性。
6. `requests==2.31.0` 的独立安全公告仍未关闭；即使本修复通过，P4 Beta/Stable 发布门槛仍须单独处理 requests 和 required reviewers。

## 2026-11-09 requests 安全修复专项（候选阶段历史记录）

> 本节记录合并前的候选状态；最终 pin、Artifact、远端 CI 和 Session 兼容性结果以末尾“Requests / cryptography 修复最终记录”为准。

**历史状态：已完成版本命中和实际调用路径评估；当时 CI 与发布审批尚未完成。** 本段不改写上文关于旧版本的历史证据。

- 当前源代码明确以 `requests.Session` 用于登录、持久 Cookie、查询、下单和撤单；订单请求的 `allow_redirects=False` 保护必须保留，且 P3 禁止对不确定交易结果自动重试。项目没有直接调用 `requests.utils.extract_zipped_paths`，也没有在生产请求中显式 `verify=False`；但 `.netrc` / TLS 行为仍受 Requests 运行时影响。
- 上游已确认三个漏洞：CVE-2024-35195（错误 TLS Session 复用，首修 2.32.0）、CVE-2024-47081（恶意 URL 下可能泄漏 `.netrc` 凭证，首修 2.32.4）、CVE-2026-25645（`extract_zipped_paths` 临时文件复用，首修 2.33.0）。命中版本 `requests==2.31.0`。
- 推荐并批准的最小修复候选 `requests==2.33.1`：覆盖上述三个修复；相对于 2.34.2 的 URL、代理和类型变更，减少一次跨发行线的行为变化。2.33.1 的头部解析和 CVE-2026-25645 测试清理修复来自上游 release notes；**这不是声称没有任何剩余漏洞**。
- 同步 `setup.py`、`ci/audit_packages.py` 的严格 Requires-Dist 契约与两个合成包审计测试；不改交易代码，不放宽固定依赖集及路径/秘密扫描。
- 增加 `tests/test_requests_compat.py`：确认真实安装版本、TLS verify 默认开启；以真实 Requests `Session.prepare_request` 无网络构造合成订单表单，并以完全合成 Session 验证交易 POST 遇 302 时只调用一次且明确禁止自动重定向。必须保留 P0 对 `Session.request/send` 的进程级禁网拦截，不挂载或绕过原有安全 guard。此测试不是对三个上游 CVE 的完整 exploit reproduction。
- 必须在同一新 Head 上完成 Build/check/docs/coverage、Offline tests（三入口 NetworkMode=none）、Package Alpha（sdist/wheel、Twine、严格审计、禁网双安装），且审查最终提交的差异；合并后再确认 master push CI。
- 由于 PyPI `0.2.6` 仍旧版发行，master 修复不代表已安装的最终用户受保护。Beta/Stable 仍受发布审批门槛和实际授权阻断。

官方公告和变更：
- https://github.com/advisories/GHSA-9wx4-h78v-vm56
- https://github.com/advisories/GHSA-9hjg-9r4m-mvj7
- https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2
- https://github.com/psf/requests/blob/main/HISTORY.md


## 2026-11-09 Requests / cryptography 修复最终记录（PR #22 合并基线）

### 最终 pin 与证据

PR #22 合并时的 master `624fc5aba6875b89202d16b5db9d6c927c48fb8b` 的 sdist/wheel Artifact manifest 与 `setup.py` 均确认：

| 直接运行依赖 | 最终 pin | 结论 |
| --- | --- | --- |
| requests | `2.33.1` | 已高于此前记录的三个公告首修版本；Session/TLS 默认、真实 Requests prepare_request、302 不重定向、订单 POST 单次等合成回归在最终 559 项 CI 中通过 |
| cryptography | `50.0.2` | 高于此前列出的 OpenSSL wheel、SECT、X.509 name constraints 等公告首修版本；RSA 生产公钥和 PKCS#1 v1.5 加密兼容测试通过 |
| rsa | `4.9` | 保持原 pin；Dependabot PR [#20](https://github.com/riiy/emtl/pull/20) 提议升级到 4.9.1，目前仍 open，尚未合并。它是单独依赖维护事项，不应借 P4 收尾自动合并 |
| ddddocr | `1.4.11` | 保持原 pin；metadata 要求 Python <3.12，当前支持范围仍限定 CPython 3.11/Linux |

Requests 2.33.1 的上游发行记录确认：2.33.0 修复 CVE-2026-25645，且 2.33.1 修复头部解析与该公告测试清理问题；2.32.0 / 2.32.4 已包含此前 CVE-2024-35195 / CVE-2024-47081 修复。来源：[Requests HISTORY](https://github.com/psf/requests/blob/main/HISTORY.md#2331-2026-03-30)。

cryptography 50.0.2 的上游变更记录确认 Linux/macOS/Windows wheels 使用 OpenSSL 4.0.3；50.0.0 已修复其 PKCS7 decrypt oracle 相关问题，50.0.2 高于本报告旧表列出的修复版本。来源：[cryptography 50.0.2 changelog](https://cryptography.io/en/50.0.2/changelog/)。

### 适用性与声明边界

- 这是对本报告所列旧公告的版本修复核对，不是完整 SBOM 扫描，也不证明当前 pin 或所有传递依赖不存在任何漏洞。
- Requests 2.33.1 不是截至本记录日 PyPI 最新版本；选择它是此前维护者批准的最小升级目标。更高版本的升级应另行评估 changelog、依赖元数据和请求行为，不在本次 P4 收尾中扩大。
- cryptography 50.0.2 的实际 Linux wheel、RSA 生产公钥/PKCS#1 v1.5 测试均由最终 master 的 CI 覆盖；不因此宣称其他 OS/Python 平台兼容。
- `rsa==4.9` 的 Dependabot PR #20 仍需单独 Review/CI 决策；当前不自动合并、不扩大本次依赖变更。
- `ddddocr==1.4.11` 与 Python 3.12+ 的兼容性问题仍然存在；本项目当前明确限制为 Python 3.11，不把 OCR 迁移混入本次收尾。
- 每月 Dependabot 仅提出 PR；所有 runtime pin 变更仍需独立审查、Offline、Package Alpha 和 API/交易行为回归。
