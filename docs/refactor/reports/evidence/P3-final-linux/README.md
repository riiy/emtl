# P3 最终 Linux 旧尝试：历史证据索引

本目录现在保存F1整理前的未完成尝试，不是最终Linux PASS或远端CI Artifact。旧尝试没有完整image identity、三份Linux JUnit、host-status或verification-summary；不能从下面的历史计划表推定测试通过。

## F1整理后的实际文件

| 文件 | 用途 |
| --- | --- |
| `plan.md` | 旧尝试原计划，原字节保留 |
| `history-before-f1.tar.gz` | 整理前25份原始文件的逐字节归档，含原README、本地基线JUnit、manifest、Git/构建日志 |
| `history-files-sha256.json` | 归档整体及每份内部原件SHA256，已逐项核验 |
| `script-relocation.json` | 两脚本原/新路径及原字节哈希、忽略规则、授权停止旧构建记录 |

两个一次性脚本原字节迁移到Git忽略的`dist/p3-f1e1/tools/original/verify_host.py`、`dist/p3-f1e1/tools/original/observe.py`；它们不是批准计划强制要求入库的正式工具。单份历史原件另保留在忽略的`dist/p3-f1e1/history-before-f1/`，交付原件以本目录归档和SHA256清单为准。未通过改写日志空白/换行来通过hooks，也未放宽lint。

归档中的baseline JUnit是旧本地467节点基线，不是本次Linux结果。首次旧构建在CLI解析阶段退出125；后续旧构建在维护者明确授权后停止。容器停止记录中的137不是测试退出码。原FAIL、旧README和日志都保留在归档中。

新的E1必须另建镜像并产生完整证据，不能把旧尝试当作成功。当前进度以P3-acceptance.md最新节为准；以下内容仅保留旧尝试原定材料与方法，不表示文件已生成或仍位于本目录。

## 旧尝试原计划材料表（历史，不表示已产生）

| 文件 | 用途 |
| --- | --- |
| `plan.md` | 独立可执行计划、边界、CLI兼容记录 |
| `workspace-before.json`、`git-*.log` | HEAD、分支、dirty/staged状态、tracked/untracked清单及diff |
| `source-sha256.json` | 与既有最终R3快照一致的46文件清单 |
| `source-tests-sha256.json` | 源码、全部测试及fixtures SHA256 |
| `copy-inputs-sha256.json`、`build-context-audit.json` | 90个非自引用COPY输入、Docker忽略规则与新增文件纳入证明 |
| `baseline-final-*-junit.xml`、`expected-nodes.json` | 本地最终467节点基线，只读归档，不冒称本次Linux执行 |
| `host-commands.json` | 实际宿主命令、cwd、起止时间、退出码与逐命令日志 |
| `docker-build.log` | 首次CLI不支持日志参数的退出125原件，未开始构建 |
| `docker-build-final.log`、`image-id.txt`、`image-inspect.log`、`image-identity.json` | 原Dockerfile无缓存新构建及实际image ID/RepoDigests/平台 |
| `network-mode.json`、`container-inspect-*.log` | 同一受测容器精确NetworkMode=none，无宿主挂载 |
| `container-full.log`、`container-logs.log` | 完整容器输出 |
| `container-state.json`、`host-status.json`、`container-cleanup.log`、`cleanup-check.log` | 退出、报告导出及仅清理本次唯一容器的状态 |
| `reports/commands.json` | 容器内所有原驱动与附加OS探针命令、cwd、退出码 |
| `reports/junit.xml`、`reports/outside-junit.xml`、`reports/explicit-junit.xml` | 三份完整Linux JUnit |
| `reports/command-03.log`、`reports/command-06.log`、`reports/command-09.log` | 默认tox、仓库外不同顺序、显式tests三入口完整日志 |
| `reports/coverage.json`、`reports/coverage.xml` | 原始coverage数据报告，非控制台摘要 |
| `reports/versions.json`、`reports/tox-result.json`、`reports/synthetic-environment.json` | 实际版本、真实tox执行与合成父环境 |
| `reports/per-entry-verification.json` | 每入口进程退出、467节点/零失败核对及前后系统探针索引 |
| `reports/image-inputs-before.json`、`reports/image-inputs-after.json` | 容器内实读的COPY输入SHA256 |
| `tox-isolation-verification.json`、`verification-summary.json` | 宿主独立解析汇总，不替代原件 |
| `evidence-sha256.json`、`SHA256SUMS` | 最终证据索引；索引本身不自包含哈希 |

## 旧尝试原定验证方式与限制（历史）

- 使用现有 `ci/offline.Dockerfile` 和 `ci/run_offline_tests.py`。`observe.py` 只观察原驱动的命令执行：每入口前后独立运行原OS探针，返回后立即解析JUnit并核对节点；不改测试、选择参数、环境隔离或生产逻辑，发生不一致即停止后续入口。
- 三个入口共享一个 `--network none` 容器；逐入口要求进程退出0，全部结束后另核容器退出0。不是三次独立的容器启动，也不是1401个独立测试。
- tox使用原驱动的固定假凭证哨兵。真实 `commands_pre` 必须在pytest启动前输出隔离成功；不以pytest已经清理环境后的断言替代。
- Docker build context为当前整个工作区 `.`，不是Git归档。`.dockerignore` 排除的生成版本/缓存不计受测输入。当前证据目录仍被COPY，但从输入哈希清单排除以避免自引用；其余源码、测试、CI、fixtures、元数据及文档全部在容器执行前后核对。验收追加的文档不在镜像中，不冒称整工作区最终文档与镜像字节相同。
- 无registry RepoDigest时仅记录实际本地content-addressed image ID，不伪称已推送/发布镜像。
- 当前源码Review PASS和17种变异均检出是维护者提供的前提；本轮不重新执行变异或代签独立Review。无真实账户/交易请求，无自动commit/push/merge；完成后等待独立复核。
