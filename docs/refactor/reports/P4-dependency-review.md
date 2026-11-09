# P4 依赖审查（2026-11-08）

## 结论

**公开 Beta / Stable 阻断：需要维护者完成已知公告的适用性评估及逐项更新/延期决策。** 本次未升级任何运行时依赖，未把“可安装/测试通过”解释为无漏洞。

## 清单与来源

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

## 已核实公开公告

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

## 下一步（未经授权不执行）

由仓库维护者逐项决定定向修补或有依据的延期，记录适用性、版本范围、风险、验证及回退；HTTP 更新须保留请求次数、重定向、异常与零重发回归，密码学更新须验证既有加密契约。再跑完整 Offline、安装产物、兼容目标和文档构建。未经解释的高严重度问题不得进入公开 Beta；不得用自动升级或自动合并跳过审核。
