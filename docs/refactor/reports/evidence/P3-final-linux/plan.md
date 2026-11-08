# P3 最终 Linux 离线验证计划

- 授权：维护者本轮明确要求只做最终 Linux 验证；当前源码独立 Review PASS、完整套件467项及17种变异检出为维护者提供的前提，本轮不重复代签Review或执行变异。
- 范围：只新增本目录的验证脚本/原始证据，向 `docs/refactor/reports/P3-acceptance.md` 追加结果；不修改生产、测试、CI、依赖或既有历史证据，不 commit/push/merge，不执行真实交易。
- 仓库：`/Users/lld/emtl`；实查HEAD为 `ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`，有8个tracked修改、10个untracked交付文件，无staged改动。HEAD不是受测源码标识，必须记录dirty工作区及文件哈希。

## 顺序与判定

1. 保存Git HEAD、分支、完整tracked/untracked清单、diff、status；对所有源码/测试（含fixture）、CI、构建配置生成SHA256。记录完整Docker COPY输入清单，检查新增 `src/emtl/errors.py`、`tests/test_trade_errors.py` 未被忽略。既有本地最终JUnit与源码manifest作为467节点/源码基线，只读复制归档并核对。
2. 使用完整当前工作区作为context，以原 `ci/offline.Dockerfile` 执行 `docker build --no-cache`，唯一新标签及 `--iidfile`；允许依赖准备联网，不运行真实账户请求。保存完整命令、cwd、退出码、日志、image inspect/ID/RepoDigests；禁止复用旧446镜像或失败后擅自改Dockerfile/依赖/使用薄层替代。
3. 仅创建本轮唯一 `--network none` 容器，无宿主挂载、无宿主凭证注入。运行原 `ci/run_offline_tests.py`，证据观察脚本只包裹其run记录函数：每个测试入口前后调用原系统网络探针；每次入口返回立即解析完整JUnit、要求467项、0 failures/errors/skipped、无重复节点且与当前本地节点集一致，否则立即停止，不执行后续入口。
4. 三入口保留原命令、顺序和环境：真实tox根默认入口（coverage）；仓库外 `/tmp` 不同文件顺序完整入口；仓库内显式 `tests/` 完整入口。不传 `-k`、`--ignore` 或跳过参数。tox沿用原合成父凭证及commands_pre，核对真实前置隔离检查在pytest前成功，不用pytest清环境后的结果替代。
5. 容器执行测试前后对源码/测试/CI/config及构建时COPY输入只读核对哈希；生成文件 `_version.py`、egg-info、字节码/缓存不计入受测输入。每入口进程退出码必须0；所有入口共享同一禁网容器，最终再要求容器退出0。保存原始三JUnit、coverage JSON/XML、tox-result、版本、逐命令完整日志、系统探针、NetworkMode、inspect、容器退出/清理状态。失败也先导出证据后仅清理本轮容器。
6. 宿主复核所有JUnit/节点、coverage完整性、tox隔离、manifest及HEAD/原文件未变。追加验收§13，保留历史446记录及原FAIL叙述。证据生成SHA256索引；说明镜像若无RepoDigest则使用本地content-addressed image ID，不冒称registry digest。

## 停止条件与边界

- 构建失败、隔离失败、凭证隔离失败、数量/节点不一致、失败/错误/跳过、报告缺失、非零容器退出或源文件漂移即停止并如实报告；不修改代码/测试来通过。
- 验证脚本不是新增CI runner，不替代原驱动或改变测试逻辑；仅提供逐入口失败即停的证据观察。
- 本次只证明本地Linux最终dirty快照的离线验证；不代表最终提交/远端CI/合并树验收，不关闭P3。完成后停止，等待独立复核。

## 执行前工具兼容记录

首次 `docker build` 在CLI解析阶段退出125：当前Docker使用legacy builder，未安装buildx，不支持仅用于日志格式的 `--progress=plain`。尚未发送context或执行Dockerfile，不属于镜像/依赖构建失败。保留 `docker-build.log`、原命令和退出码；证据脚本只移除此显示参数，以原Dockerfile、完整context、同一唯一新标签和 `--no-cache` 实际构建，日志改名 `docker-build-final.log` 避免覆盖。无项目配置/依赖改动，不使用旧镜像替代。
