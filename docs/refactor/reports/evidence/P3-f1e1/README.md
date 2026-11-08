# P3 F1/E1 最终本地交付证据（2026-11-08）

本目录是未提交工作区的实际原始证据，不是远端CI Artifact，也不把HEAD当作受测源码标识。原Review FAIL和旧446/467结果均保留；旧尝试见[历史索引](../P3-final-linux/README.md)。

## 结果

- F1完整103文件候选树（含untracked）及真实工作区pre-commit全部通过；11个待提交Python文件直接Ruff/Black、diff检查通过，没有改规则、批量noqa或交易生产/测试代码。
- E1使用原`ci/offline.Dockerfile`、当前dirty源码、`docker build --no-cache`新建镜像；ID为`sha256:2150b9bc9fe31e0785163731ccd487853810ed6c33411d5769d2ab6983e05a9b`，tag为`emtl-p3-final-linux:197eec73af7d`，平台linux/amd64。
- 原批准的三个入口顺序/参数不变：默认tox覆盖率、仓库外不同文件顺序、仓库内显式tests/；各467项，零failure/error/skip，节点集合与R3基线相同。是同一467节点的三轮运行，不是1401个独立测试。
- 唯一容器NetworkMode=none、无宿主挂载/真实凭证注入；7次独立OS探针通过，tox commands_pre在pytest启动前确认account environment isolated。容器退出0，报告复制/清理均退出0，唯一容器确认已不存在；镜像保留供人工核验，未push/publish。
- 95项源码/全部测试/fixtures/CI/config/文档COPY输入在容器前后与锁定宿主哈希一致；46文件R3保护快照一致。测试完成后只有验收与交付索引/归档新增或更新，不声称最终文档与受测镜像字节完全相同。

## 实际文件

| 文件 | 含义 |
| --- | --- |
| `raw-evidence.tar.gz` | 122份F1/E1原件，保留实际字节，不为文本hooks重写日志/XML/JSON |
| `raw-files-sha256.json` | 归档SHA256及每个原件SHA256；已打开归档逐项重新计算验证 |
| `SHA256SUMS` | 归档与成员索引文件的SHA256；不自引用 |
| `delivery-inventory.json` | 最终建议提交文件清单（含原有P3未提交实现）；不含dist临时工具、缓存、环境或散落日志 |
| `delivery-checks.tar.gz` | 封存后的质量门槛/静态扫描/链接及来源复核原件和临时交付工具审计副本；检查快照早于最终收尾文档，最后完整交付树另复核 |

## 归档内可核验路径

- `f1/f1-complete-tree/commands.json`、`command-05.log`：首次隔离复制丢失可执行位造成EXE001，原工作区未变；保留FAIL。
- `f1/f1-preserve-modes/result.json`、`commands.json`及全部命令日志：保留权限后完整质量门槛PASS、候选清单/哈希、真实index与文件未变。
- `f1/old-build-stop.json`、`old-build-*.log`：维护者授权停止旧构建；137只是停止状态，不是测试结果。
- `e1/workspace-before.json`、`git-*.log`：HEAD、分支、tracked/untracked/staged和完整diff。
- `e1/source-sha256.json`、`source-tests-sha256.json`、`copy-inputs-sha256.json`、`expected-nodes.json`：保护源码、源码/全部测试/fixtures、95 COPY输入和467节点基线。
- `e1/build-context-audit.json`、`input-audit-clarification.json`：实际context及继承旧脚本标签的澄清；本轮旧历史证据5文件也全部纳入95项哈希。
- `e1/host-commands.json`、`docker-build-final.log`、`image-id.txt`、`image-inspect.log`、`image-identity.json`：新构建真实命令/cwd/时间/退出码及镜像身份。RepoDigests仅为本地daemon报告，不声称发布。
- `e1/attachment-sha256.json`、`attachments/`：原字节observer及两个锁定附件的哈希；附件显式复制到/p3-evidence，不修改原驱动/镜像源码，不是新增正式runner。
- `e1/network-mode.json`、`container-inspect-*.log`、`container-state.json`、`host-status.json`、`container-*.log`、`cleanup-check.log`：网络、完整inspect/输出、退出和清理证据。
- `e1/reports/junit.xml`、`outside-junit.xml`、`explicit-junit.xml`：三份完整JUnit；`coverage.json`、`coverage.xml`为第一入口的完整coverage报告（后两入口按原计划不采coverage）。
- `e1/reports/commands.json`、`command-*.log`、`versions.json`、`tox-result.json`、`synthetic-environment.json`：全部容器命令及日志、真实tox/版本/合成凭证父环境。
- `e1/reports/per-entry-verification.json`、`observer-status.json`、`image-inputs-before.json`、`image-inputs-after.json`：每入口即时节点验证、观察状态及容器实读哈希。
- `e1/tox-isolation-verification.json`、`verification-summary.json`：宿主独立解析汇总；不替代以上原件。
- `e1/evidence-sha256.json`、`SHA256SUMS`：E1原件内层索引；外层raw-files索引再覆盖这些索引的字节。
- `tools/`：本轮实际一次性操作脚本的审计副本，原字节封装在归档；可执行临时副本仅在Git忽略的dist工具目录，不作为正式可复用Python工具交付。

版本：Python 3.11.18、tox 4.67.13、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2。Coverage JSON报告综合94.44%、语句95.20%、分支91.23%，不把不同指标混称总覆盖率。

## 验证与边界

先按SHA256SUMS核对归档/索引，再只读打开tar逐成员核对raw-files-sha256.json；路径必须是相对路径、无`..`、无链接。无需运行归档里的临时脚本，也不需要网络或真实凭证。完整历史归档另有其独立SHA256清单。

delivery-checks.tar.gz内的checks-files-sha256.json覆盖其余所有成员（不自引用）；外部SHA256SUMS覆盖补充归档。最终清单自身不自哈希；最终收尾文档不在受测镜像/早期检查快照中，但原源码/测试/CI/config始终受哈希保护。无需为了文档/索引自引用反复构建测试镜像。

凭证检查包括候选文件与归档成员的静态模式扫描，以及credential-like Python字面量核验为合成测试哨兵；不读取真实账户环境，不把静态扫描宣称为对未知秘密的数学证明。最终交付质量复核记录见P3-acceptance.md §13；最终PR/head_sha/双CI/Artifact/Tree仍需维护者受控提交后核验，不由本轮本地结果替代。
