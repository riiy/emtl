# P2 实施与阶段验收记录

## 1. 状态与授权

- 日期：2026-11-07；分支 `refactor/p2-client-isolation`；开始 HEAD `e35cf1782c4dded98fc4ce2ad3dce4c56648e28a`。
- 本次工作为未提交修改，HEAD 不能代表全部实现；最终代码快照/镜像证据在后续节记录。
- 维护者明确批准 `docs/refactor/plans/P2-plan.md` 设计并授权实施，随后确认“P1 已有最终 Review PASS”。该历史签认为维护者提供的信息，本次未取得其原始审查路径，不冒称独立重审。
- 仅 P2；不真实登录/查询/交易、不用真实凭证、不自动 commit/push/tag/发布。P2 需求与 P2 计划开始时均为既有未跟踪文档，保留并检查。
- **最终结论：PASS（2026-11-07）。**
P2 已完成最终远端 CI 验证、独立 Review，
并通过 PR #5 合并至 master。
最终验收证据见第 8 节。
第 2–7 节保留实施期间的历史记录，
其中 342 passed 和 NEEDS EVIDENCE
均属于相应历史阶段的实际状态。

## 2. 修改范围

| 文件 | 内容 |
| --- | --- |
| `src/emtl/client.py` | 显式绑定账户的同步客户端；实例 Session/jar/token/OCR；认证状态机与 close |
| `src/emtl/_coordination.py` | 按账户共享 RLock，弱账户/资源登记，拒绝活动资源共用 |
| `src/emtl/_protocol.py` | 无状态请求字段、token提取、OCR转换、行情/响应解码 |
| `src/emtl/core.py` | 保留旧状态/认证/私有接缝；委托无状态 helper，不改旧失败策略 |
| `src/emtl/__init__.py` | 末尾新增 TradingClient 导出 |
| `tests/client_helpers.py`、五个 `test_client_*.py` | 合成 Session/OCR、内存 adapter、并发/认证/业务/生命周期/日志矩阵 |
| `tests/conftest.py` | 新增 client_factory，原隔离 fixture 不变 |
| `tests/test_api_contract.py` | 精确追加导出期望，新类签名；旧签名/身份/顺序断言保留 |
| `tests/test_test_safety.py` | 新增未配置客户端命中 P1 guard 的负向验证 |
| `docs/refactor/contracts/P2-client-api.md`、`docs/reference/emtl.rst` | 新接口与安全/兼容边界、文档链接 |
| `docs/refactor/plans/P2-plan.md`、本文 | 批准/S0记录、实施结果与剩余风险 |

不修改 endpoint、utils/CLI、打包元数据、依赖、tox、网络 guard、Dockerfile、workflow 或历史 P1 证据。

## 3. 分批执行与已验证结果

所有 macOS pytest 命令均以仓库根为 cwd，加 `PYTHONDONTWRITEBYTECODE=1` 与系统禁网。此处列出已经实际运行的命令及结果，不将待执行项目标为通过。

### S0

- Python 3.11.14；pytest9.2.0、pytest-cov7.1.0、coverage7.17.2、tox4.67.12、requests2.31.0。
- `sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))'`：退出1，PermissionError/Operation not permitted，预期OS阻断，不是 suite 失败。
- `PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -q`：改动前退出0，**168 passed in 7.28s**。

### S1–S5

- 最小切片：相同命令前缀加 `tests/test_client_concurrency.py -vv`：退出0，4 passed in0.09s，含K1的POST及JSON两阶段。
- 所有权/关闭：加 `tests/test_client_lifecycle.py tests/test_client_concurrency.py -q`：退出0，17 passed in0.28s。
- 共享逻辑初提取：全套退出0，185 passed in7.85s。
- 认证矩阵：加 `tests/test_client_auth.py tests/test_client_lifecycle.py tests/test_client_concurrency.py tests/test_auth.py tests/test_logging_safety.py -q`：退出0，85 passed in2.32s。
- 扩展业务及并发：第一次加 `tests/test_client_operations.py tests/test_client_concurrency.py -q` 退出1，100 passed/11 failed/8 errors。问题是测试观测锁未恢复，跨用例再次包装代理造成 AttributeError；没有关闭防护/删测试。改为 monkeypatch 自动恢复后，加 `tests/test_client_operations.py tests/test_client_concurrency.py tests/test_client_auth.py tests/test_client_lifecycle.py -q`：退出0，156 passed in1.06s。
- 导出/日志/安全集合后全套：退出0，**342 passed in9.39s**。此结果早于最终格式修正，最终快照的 tox/Linux 结果另列，不混淆版本。
- 初次 Ruff/Black 检查退出1，发现新增代码格式/测试断言风格及合成token字面量警告；仅修本次文件。修正后 Ruff 退出0，未更改项目规则；严格整数Status门槛保留一处有说明的 E721 noqa（禁止bool/float通过），不弱化运行时判断。

## 4. 风险测试与 P1 等价保持

| 验证对象 | 实际用例与证据位置 |
| --- | --- |
| 同账户跨实例串行，响应解析也持锁 | `test_client_concurrency.py::test_kill_same_account_serializes_across_instances[post/json]`；真实原锁非阻塞竞争正向事件 |
| 异账户HTTP真正重叠 | `test_kill_different_accounts_enter_http_together`，双线程Barrier，不用sleep/计时比 |
| PreparedRequest Cookie/token/header隔离 | `test_kill_sessions_tokens_and_prepared_cookies_never_cross`，独立内存adapter，无真实transport |
| 完整认证+查询+下单+撤单两账户链 | `test_full_authentication_and_order_chains_never_cross_accounts`，独立OCR/Session/token/jar及core状态不变 |
| 混合操作、重入与失败后释放 | `test_same_account_serializes_mixed_operations`、`test_failed_operation_releases_lock_without_corrupting_another_instance` |
| 登录失败清旧态与显式恢复 | `test_client_auth.py`，Status类型矩阵、无token、全部认证阶段异常；旧 `test_auth.py` 不改 |
| 无重复资金副作用 | `test_client_operations.py::test_uncertain_submission_never_replays_or_compensates`，提交事件一次/POST一次/无补偿GET；JSON1/JSON2/text异常独立断言 |
| 重定向不隐式重发 | `test_redirect_cannot_resend_order_at_adapter_level`，create/cancel×307/308，实际PreparedRequest一次adapter.send |
| 六查询、表单/JSON身份/撤单/行情 | `test_client_operations.py` 请求与返回矩阵、新旧对照；保留原core/orders/wrapper用例 |
| 生命周期/弱表/资源拒绝 | `test_client_lifecycle.py`，close幂等/失败最终关闭、全部公共方法关闭后零HTTP、并发首次构造、历史身份回收 |
| 主动日志与错误安全 | `test_client_logging.py` + 原日志安全测试；检查全部LogRecord字段，不复制异常内容 |
| 安全底座 | 原guard/恢复/CLI/tox/CI故障注入测试保留；新增 `test_new_client_unconfigured_http_is_guarded` |

P1节点迁移：原168项不删除、不skip，不改变旧私有monkeypatch接缝。唯一已有期望调整是 `test_exports_and_signatures` 的精确 `__all__` 末尾追加类；新增测试函数不替代原分支。逐函数、逐原测试函数的接缝映射仍以计划第10–11节为准，实际采用“保留旧seam，增加新实例工厂镜像测试”。None wrapper seam只证明返回契约，不计作HTTP/不重试证据。

## 5. 实施偏差与边界

1. 共享协议helper与六查询/订单薄包装在同一编辑批次落地；先通过认证集合，再验证业务集合，最后导出完整类。未跳过先行Kill Test门槛，也未改变已批准接口/旧认证策略。
2. 内存传输测试需在特定测试实例上绑定P1保存的原始Session.request与send（两者都被guard拦截）；所有http/https adapter均为纯内存BaseAdapter，全局guard与OS禁网不恢复。只恢复send不足以生成PreparedRequest，故比原计划文字更明确地同时绑定两个实例方法。
3. 失败清理保留主异常；仅抑制已有主异常时的次级close/clear错误，不输出错误内容。close即使清理失败仍CLOSED，重复不再次关闭。
4. 保留既有CI输出目录 `dist/p1-offline` 与artifact命名，不为P2重写CI；本次结果必须由新镜像/日志/nodeids对应，不能拿P1历史报告冒充。
5. 原Dockerfile准备镜像实际构建成功，但其3个Python文件早于最终headers收口。按计划追加第21节，用已准备镜像加禁网COPY薄层取得最终源码，所有依赖/原CI配置不变；用基础镜像层前缀与34文件SHA256证明不是未经核对的混合快照。此为本地验证准备调整，最终远端CI仍必须按既有workflow重新构建。

## 6. 完整 tox / Linux / 最终审查

### 6.1 macOS 系统禁网完整验证

工作目录 `/Users/lld/emtl`，`dist/p2-local/command.json` 保存实际参数/cwd/退出码，`tox.log` 保存原始日志。父环境仅注入固定合成值 `P2_FAKE_VALUE`，键为 `EM_USERNAME/EM_PASSWORD/EM_P2_SENTINEL/P0_FAKE_ACCOUNT_CREDENTIAL/P1_FAKE_ACCOUNT_CREDENTIAL/NETRC/SSH_AUTH_SOCK/SSH_AGENT_PID`；另设 `PIP_NO_INDEX=1`、`TOXPYTHON=/Users/lld/emtl/.venv/bin/python`、`PYTHONDONTWRITEBYTECODE=1`。真实 tox precheck 在 pytest bootstrap 之前输出 `account environment isolated`。

实际 tox 命令：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p2-local/tox-result.json -- python -m pytest --cov --cov-report=term-missing --cov-report=xml:dist/p2-local/coverage.xml --cov-report=json:dist/p2-local/coverage.json --junitxml=dist/p2-local/junit.xml -vv
```

退出 **0**，**342 passed in 16.62s**；不是将不同入口累计成不同用例。JUnit、coverage XML/JSON、tox-result均已实际保存。

仓库外/不同文件顺序：cwd为 `/private/var/folders/0k/2wdc58817qj3v6mcyst_x6ww0000gn/T/opencode`；绝对Python、测试路径，仍使用sandbox禁网。先运行client logging/lifecycle/auth/concurrency/operations，然后旧orders/auth/core，再按文件名追加所有其它根测试。完整实际命令见 `dist/p2-local/outside-command.json`；原日志 `outside.log`、`outside-junit.xml` 均已保存。退出 **0**，**342 passed in 17.45s**，未累计第一轮覆盖率。

覆盖率仅观察：行 **386/408=94.61%**，分支 **71/80=88.75%**，综合 **93.65%**；core与共享protocol全部行/分支覆盖，client尚缺非法Session/OCR及无主异常的Cookie清理错误等小分支。不把总体覆盖率当作并发或不重发证据。

P1保留审计：历史 `dist/p1-repair/junit.xml` 的168个 `(classname,name)` 均存在于新342项JUnit；12个未计划修改的原测试Python文件与HEAD逐字节一致。证据为 `dist/p2-local/p1-nodeid-preservation.json`。三处已有测试设施的diff仅增加fixture/新测试，以及明确批准的精确导出期望。

`dist/p2-local/source-sha256.json` 记录本次34个生产/测试/CI Python文件（排除生成_version及缓存）的SHA256；后续检查与之匹配。`document-checks.json`保存文档结构/链接和源码哈希核对结果。

#### 请求 headers 所有权收口后的最终 macOS 快照

自检进一步确认旧验证码/token GET原来直接传基础headers对象。为同时遵守新客户端“每请求独立headers”和旧可观察行为，两处共享helper增加可选headers参数：旧入口仍传原基础对象，新类显式传副本；认证用例新增对象身份断言。此修正未改变请求字段/值/timeout，也没有改变旧层行为。

随后以相同tox命令、父合成环境和OS禁网重新运行，只将报告目录替换为 `dist/p2-local-final`。退出 **0**，**342 passed in14.27s**。该目录实际包含 `command.json`、`tox.log`、`tox-result.json`、JUnit、coverage XML/JSON及更新后的34文件 `source-sha256.json`。

最终macOS快照覆盖率：行 **387/409=94.62%**，分支 **71/80=88.75%**，综合 **93.66%**。此前 `dist/p2-local` 及仓库外结果是headers收口前的历史快照，不冒充最终快照；Linux必须再核对与最终源码哈希一致后才可作为最终证据。

### 6.2 变异检验（只在隔离子进程内存生效）

- 将所有账户映射到一条共享entry：K2因不同账户entry身份断言失败，退出1、1 failed in0.19s，符合预期。
- 保持账户entry不同，但在实际 `_protocol.query` 外包一把全局HTTP锁：K2因Barrier无法被两个请求同时到达而抛BrokenBarrierError，退出1、1 failed in5.62s，符合预期。证明测试不只检查锁对象身份，也能检出真正的全局HTTP串行瓶颈。
- 命令、真实退出码和原日志分别保存为 `dist/p2-local/global-lock-mutation.{json,log}`、`http-lock-mutation.{json,log}`；没有写入生产源码或让变异进入正常测试进程，不把预期失败称为完整suite失败。

### 6.3 静态与修改范围审查

以下实际退出均为0，日志及参数保存在 `dist/p2-local/quality-commands.json` 与同目录对应log：

```bash
.venv/bin/ruff check --no-cache src/emtl tests conftest.py
.venv/bin/black --check src/emtl tests conftest.py
.venv/bin/ruff --version
.venv/bin/black --version
git diff --check
git diff --cached --check
```

已逐份读取新生产文件、并发/内存传输/日志测试及tracked差异；未把git diff --stat当作untracked审查。此为实施者自检，不冒称独立Review。最终文档补记后再核对修改范围与空白。

最终补记后再次实际运行Ruff、Black、tracked/staged空白检查，均退出0；核对全部tracked与untracked清单。最终34文件仍与受测镜像哈希一致，38份Linux原始证据哈希全部通过；三份P2 Markdown的代码围栏/空白及两条reference下载链接检查通过，结果保存为 `dist/p2-local-final/final-document-checks.json`。生产/测试/CI源码在最终受测快照后未再改变；需求、原CI/guard/tox/打包/CLI/const/utils未改，未暂存或提交。

### 6.4 Linux 与远端证据

#### 构建、失败记录与最终受测身份

- `docker build --file ci/offline.Dockerfile --tag emtl-p2-offline:local .` 实际退出 **0**，镜像 `sha256:d14e4c0af3220e0ffc3060010ba06b73434d65d228c92736da5971140a58b462`，linux/amd64。构建准备允许联网，执行期不联网。原日志与真实结果保存在 `dist/p2-linux/docker-build.log`、`docker-build-result.json`。
- 以独立 `--network none` 哈希容器实查，发现 `src/emtl/_protocol.py`、`src/emtl/client.py`、`tests/test_client_auth.py` 三文件与最终工作区不同；完整比较为 `initial-image-comparison.json`，未用该镜像直接进行最终验收。
- 最终薄层构建命令为 `docker build --network none --file - --tag emtl-p2-offline:final .`，stdin如下；没有修改仓库Dockerfile：

```dockerfile
FROM emtl-p2-offline:local
WORKDIR /workspace
COPY src/ src/
COPY tests/ tests/
COPY docs/ docs/
```

- 第一次薄层构建的宿主120秒上限在COPY阶段触发TimeoutExpired，包装器退出1，不能将其当作成功，也无法据此报告Docker命令本身的正常退出码。原日志 `docker-build-final.log` 和 `docker-build-final-timeout.json` 保留。随后只延长本地构建等待上限为900秒（不改任何HTTP timeout），重跑退出 **0**，完整stdin/参数/结果保存在 `docker-build-final-retry-result.json`、原日志 `docker-build-final-retry.log`。
- **最终受测镜像：`sha256:18917d38237a8c8511de77052e272723450fcf7a94a2e6eb85cdf6707c4631e4`，linux/amd64。** `final-image.json` 与 `prepared-image.json` 实查其基础RootFS层前缀一致。
- 最终镜像、macOS最终manifest、当前工作区的全部 **34个生产/测试/CI Python文件SHA256一致**，排除构建生成的_version和缓存。`final-image-source-sha256.json`、`final-image-comparison.json` 为实际导出结果。按路径排序、紧凑JSON编码的源码摘要清单SHA256为 `a904561be189f421877c560b9b17bba4139e0a35678b048b683f9178bf9265f4`。
- 文档验收补记不在Python源码清单内，最后更新的报告自然不属于受测镜像内容；不声称整个工作区或构建产物逐字节相同。

#### 宿主实际运行与报告导出

工作目录 `/Users/lld/emtl`；没有宿主挂载、没有 `-e` 真实凭证。以下实际参数与各退出码均保存于 `dist/p2-linux/host-commands.json`：

```bash
docker create --name emtl-p2-final-7ee0797418 --network none sha256:18917d38237a8c8511de77052e272723450fcf7a94a2e6eb85cdf6707c4631e4
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p2-final-7ee0797418
docker start --attach emtl-p2-final-7ee0797418
docker inspect --format '{{.State.ExitCode}}' emtl-p2-final-7ee0797418
docker logs emtl-p2-final-7ee0797418
docker cp emtl-p2-final-7ee0797418:/workspace/dist/p1-offline/. dist/p2-linux/reports
docker rm -f emtl-p2-final-7ee0797418
```

NetworkMode精确为 `none`，容器实际退出 **0**。先导出所有原始报告再删除本次创建的具名容器，无误删既有容器。宿主状态 `original=0 logs=0 inspect=0 copy=0 cleanup=0 evidence=0`，保存在 `host-status.txt`；网络模式、容器日志与退出码均独立保存。

| 容器内检查 | 结果 | 原始证据 |
| --- | --- | --- |
| 不依赖pytest guard的Linux OS网络探针 | 退出0，`OS network namespace isolation verified` | `reports/command-00.log` |
| 实际tox在bootstrap前隔离合成父凭证 | 退出0，`account environment isolated` | `reports/command-02.log` |
| 默认入口完整tox | **342 passed in19.85s**，退出0 | `reports/junit.xml`、tox-result、command-02.log |
| 仓库外 `/tmp`、不同文件顺序完整suite | **342 passed in14.02s**，退出0 | `reports/outside-junit.xml`、command-03.log |
| 显式 `tests/` 完整入口 | **342 passed in13.33s**，退出0 | `reports/explicit-junit.xml`、command-04.log |
| 三份JUnit实查 | 各342 tests、0 failures/errors/skipped；节点集合一致且保留旧168项 | `verification-summary.json` |
| 行/分支覆盖 | 387/409=94.62%，71/80=88.75%；综合93.66% | `reports/coverage.json`、coverage.xml |

这三轮是同一342项套件，不累计为1026项不同测试。Linux实际版本：Python **3.11.18**、pytest **9.2.0**、pytest-cov **7.1.0**、coverage **7.17.2**、tox **4.67.13**，来自 `reports/versions.json`，不根据macOS版本推断。Ruff0.4.1/Black24.4.0检查属于macOS，不冒称在容器内执行。

容器CMD沿用既有 `python ci/run_offline_tests.py`。真实完整tox/两轮pytest命令、cwd、退出码保存在 `reports/commands.json`；合成父环境为既有驱动创建的 `P1_FAKE_VALUE`（不是实际账户），`PIP_NO_INDEX=1`，没有执行期下载。报告目录虽名为p1-offline，数据实际来自上述最终P2镜像。

所有Linux原始证据已导出到宿主 `dist/p2-linux/`，包括38个文件的 `evidence-sha256.json` 索引、构建日志/失败记录、镜像与源码比较、network-mode/host-status、三份JUnit、coverage、工具版本、完整命令、tox结果、合成环境及五份容器步骤日志。`verification-summary.json` 为本次实际解析/核验后的摘要，不代替原始报告。

**交付限制：`dist/` 被Git忽略，当前是本机原始证据，不是已提交或远端artifact。** 清理工作区前应保留该目录；后续远端CI需保存对应最终提交的artifact并在本报告追加真实链接，不得仅凭本地路径宣称版本控制/远端交付完成。

远端P2 CI/artifact与独立Review尚未执行；本次不自动push或触发workflow。

## 7. 剩余风险与最终验收条件

- 真实券商认证/Status/多会话有效性均未知；仅执行批准的本地保守门槛，不用实盘补证据。
- 同账户仅按strip后用户名判断；无别名识别/跨进程/跨设备调度保证。旧API与新实例混用不保证统一串行。
- 旧认证无token保旧态、旧默认redirect、HTTP裸raise、OCR递归、现有timeout缺失为明确保留的遗留边界；资金异常可能代表服务端已受理。
- 工厂可信且资源独占、无共享adapter/retry/hook是使用契约；不能防御工厂任意代码或外部私自修改私有状态。
- P1 PASS为维护者确认，本次未重审其原件；远端P2 CI与独立Review均须另行完成。
- 最终验收要求：全部风险断言通过、最终快照Linux禁网三入口通过并保存报告、维护者批准交付后远端CI/artifact可核验、独立Review PASS。未满足不得宣布P2最终完成。


## 8. P2 最终远端验收与关闭记录（2026-11-07）

### 8.1 最终代码与合并版本

- PR：https://github.com/riiy/emtl/pull/5
- 最终受测提交：`6e2078f7dce9f255d60ce89699d405efc09e0e2f`
- 合并提交：`d46a83ac97e9a5c17839bbf514a616484dbb9225`
- 受测与合并提交的 Git Tree SHA 均为：
  `eaf1866ae6fff6c754179feec2626b759e6e38c6`

已通过 GitHub Git Commit 元数据核对两个 Tree SHA 完全一致。
该证据证明两次提交对应的已版本化文件树相同，
不代表构建产物或运行环境逐字节相同。

### 8.2 最终 GitHub Actions

| 工作流 | Run ID | 结果 |
| --- | --- | --- |
| Offline tests | [42349163949](https://github.com/riiy/emtl/actions/runs/42349163949) | success |
| Build | [42349163936](https://github.com/riiy/emtl/actions/runs/42349163936) | success |

- 两个 Run 均由 `pull_request` 事件触发。
- 两个 Run 的 `head_sha` 均为最终受测提交 `6e2078f7...`。
- Offline Artifact：
  [13563959800](https://github.com/riiy/emtl/actions/runs/42349163949/artifacts/13563959800)
- Artifact 名称：`offline-test-evidence`。

远端原始证据已经核验：

- Docker `NetworkMode=none`。
- Linux 系统级网络隔离探针通过。
- 容器退出码为 0。
- 宿主报告收集及清理状态全部为 0。
- 三份 JUnit 均为 350 tests，0 failures，0 errors。
- 行覆盖率：387/409 = 94.62%。
- 分支覆盖率：71/80 = 88.75%。
- 综合覆盖率：93.66%。

三份 JUnit 是同一测试套件的不同执行入口，
不累计为 1050 个独立用例。

### 8.3 Cookie 清理测试补强

最终测试总数由历史阶段的 342 项增加至 350 项。

新增 8 个测试重点验证：
认证 POST 或 Token GET 过程中新增 Cookie 后，
如果认证被拒绝、无有效 Token 或发生异常，
当前客户端必须清除相应认证状态。

独立 Review 已验证：
将失败清理逻辑临时替换为 no-op 后，
新增 8 项测试全部因残留 Cookie 断言而失败。

该变异没有保留在生产代码中。

### 8.4 最终独立 Review

结论：**PASS**。

审查未发现以下方面的新增阻断性缺陷：

- 不同账户的 Session、Cookie、Token 隔离。
- 同账户跨实例串行、不同账户允许并行。
- 下单、撤单发生异常时自动重复发送。
- 原公共 API / CLI 兼容性。
- P0/P1 既有离线安全网回归。

此结论仅覆盖 P2 批准范围和离线合成测试契约，
不证明真实券商认证协议、多会话有效性、
跨进程协调或实际交易结果正确性。

既有风险继续按照第 7 节记录，
不因 P2 PASS 自动视为已解决。

### 8.5 P2 关闭结论

P2 状态：**PASS，已合并至 master**。

S0–S7 的批准范围已完成实施与验收。
第 2–7 节的历史测试、镜像、路径、
NEEDS EVIDENCE 和未执行远端 CI 等描述
保留为当时状态，不追溯改写。

后续工作应重新定义独立阶段，
不继续扩大 P2 实施范围。
