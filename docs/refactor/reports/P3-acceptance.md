# P3 实施与阶段验收记录

> **最终状态（2026-11-08）：PASS — 已完成并合并至 master。** 最终远端验收与阶段关闭依据见§14。
>
> §1–§13按当时事实保留；其中的FAIL、NEEDS EVIDENCE、待交付/待复审和未提交状态均为历史记录，不代表§14签认后的最终状态。

## 1. 结论与授权

- 日期：2026-11-07；分支 `refactor/p3-trade-errors`；开始 HEAD `ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`。本次为未提交实现，HEAD 不包含本次代码。
- 维护者在停止提示后明确回复“确批准计划”，整体批准 [计划](../plans/P3-plan.md) A1–A7并授权实施。开始只有未跟踪的计划；无 tracked/staged 修改。
- **当前状态：本轮F1/E1限定交付阻断项已完成本地验证，等待人工交付/独立复核。** 维护者明确确认交易生产及R1–R3功能Review已通过，该信息是本轮输入，不冒称本轮重新审查；467项本地功能证据保留在§12。本轮仅整理交付与重建Linux证据，实际结果在§13追加，不改写原FAIL或历史446/467记录，不自动提交/推送。
- 全部测试为合成账户、内存 HTTP/OCR、P1 guard 与系统禁网；未执行真实登录/查询/交易，未读取真实账户秘密，没有 commit/push/发布或触发 CI。

## 2. 修改文件与行为

| 文件 | 修改 |
| --- | --- |
| `src/emtl/errors.py` | 两个并列 RuntimeError：TradeOutcomeUnknown / BrokerHTTPError，白名单字段、安全构造与消息 |
| `src/emtl/client.py` | 仅新客户端 HTTP 策略；局部发送标记、私有交易 helper；已尝试后普通异常安全转换，原锁和成功返回不变 |
| `src/emtl/_protocol.py` | query 仅新增默认关闭的 on_post_start 回调，紧贴取得 post callable 后的唯一 POST；旧检查/解码不变 |
| `tests/test_trade_errors.py` | 公开错误契约、K1–K4、认证/交易计数、前置/响应/状态/生命周期边界 |
| `tests/test_client_operations.py` | 精确迁移新异常预期，保留原节点；内存 adapter Timeout/redirect 与默认零重试配置 |
| `tests/test_client_auth.py` | 仅三个 HTTP 失败预期改为 BrokerHTTPError；保留清状态、原非HTTP异常身份与请求计数 |
| `tests/test_client_logging.py` | 精确新类型、str/repr/args/字段/标准 traceback 和全部 LogRecord 脱敏 |
| `tests/test_client_concurrency.py` | 新增 JSON2/text 失败仍持锁、真实竞争后释放另一实例的确定性测试 |
| `docs/refactor/contracts/P3-trade-errors.md` | 新公开失败契约、边界、安全/兼容范围及调试代价 |
| `docs/refactor/contracts/P2-client-api.md`、`docs/reference/emtl.rst` | 标注 P3 覆盖部分失败语义，链接新契约 |
| `docs/refactor/plans/P3-plan.md` | 批准、实测批次与偏差追加；保留起草事实 |
| `docs/refactor/reports/evidence/P3-local/mutations.py`、本文 | 测试专用内存变异复现脚本、实际证据及剩余项 |

没有修改 core、__init__、_coordination、CLI、endpoint/表单、旧测试、依赖/元数据、guard、tox、Docker/CI或timeout/retry策略。两交易签名、包级导出、旧普通/活跃上下文裸 raise、旧认证保旧 token 的特点保持。

## 3. 实测批次与命令

工作目录 `/Users/lld/emtl`。测试统一前缀（不是裸 pytest）：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider
```

| 批次 | 前缀后的选择/参数 | 真实结果 |
| --- | --- | --- |
| S0 基线 | `-vv --junitxml=dist/p3-local/baseline-junit.xml` | 退出0；350 passed，9.52s |
| S1 先行红灯 | `tests/test_trade_errors.py -vv --junitxml=dist/p3-local/s1-red-junit.xml` | 退出1；21 passed / 4 failed；K2两交易Timeout、K3 JSON2/text仍原异常，不是导入错误 |
| S2 HTTP/边界 | `tests/test_client_auth.py tests/test_client_operations.py tests/test_core.py tests/test_orders.py -k 'not uncertain_submission_never and not order_bad_response and not order_each_json and not cancel_text_failure_propagates_once and not redirect_cannot' -q --junitxml=dist/p3-local/s2-junit.xml` | 退出0；199 passed；暂未接入交易转换，定向选择不是最终跳过 |
| S3 交易闭环 | `tests/test_trade_errors.py tests/test_client_operations.py tests/test_client_auth.py tests/test_client_logging.py -q --junitxml=dist/p3-local/s3-junit.xml` | 退出0；176 passed |
| S4 完整矩阵 | `-q --junitxml=dist/p3-local/s4-junit.xml` | 退出0；441 passed，13.09s（早于最终新增post属性失败边界测试） |
| 最终 macOS | `--cov --cov-report=term-missing --cov-report=xml:dist/p3-local/coverage.xml --cov-report=json:dist/p3-local/coverage.json --junitxml=dist/p3-local/final-junit.xml -vv` | 退出0；442 passed；JUnit时间15.146s，0 failures/errors/skipped |

沙箱独立探针：`sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))'` 退出1，PermissionError/Operation not permitted，为预期内核阻断，不是 connection refused；未访问外部服务。

本机版本：Python3.11.14、pytest9.2.0、pytest-cov7.1.0、coverage7.17.2、tox4.67.12、requests2.31.0、urllib3 2.8.0、Ruff0.4.1、Black24.4.0。原始 `versions.json`、最终参数/cwd/退出码 `final-command.json`、JUnit/coverage/日志在 `dist/p3-local`；S0日志在 `dist/p3-baseline.log`。

最终 macOS行覆盖442/465=95.05%，分支98/108=90.74%，综合94.24%。只作观察，不作为资金安全验收标准。

归档变异脚本复跑后，另以同一sandbox执行真实tox，父进程仅注入`P3_FAKE_VALUE`合成哨兵（EM_USERNAME/EM_PASSWORD/EM_P3_SENTINEL/P0_FAKE_ACCOUNT_CREDENTIAL/P1_FAKE_ACCOUNT_CREDENTIAL/NETRC/SSH_AUTH_SOCK/SSH_AGENT_PID），设置PIP_NO_INDEX=1与本机TOXPYTHON：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p3-local/tox-result.json -- python -B -m pytest -p no:cacheprovider --junitxml=dist/p3-local/tox-junit.xml -vv
```

退出0，**442 passed in16.22s**；真实commands_pre在pytest清环境前输出`account environment isolated`。完整环境设置、cwd/参数/退出码与日志为`tox-command.json`、`tox.log`、`tox-result.json`。未用清环境后的pytest断言替代tox隔离。

Ruff/Black 首次检查指出新增测试3项断言风格和4文件排版；仅修本次新增片段，未改变工具规则。随后下列检查退出0：

```bash
.venv/bin/ruff check --no-cache src/emtl tests conftest.py
.venv/bin/black --check src/emtl tests conftest.py
git diff --check
git diff --cached --check
```

## 4. 风险测试与历史节点保持

| 关键风险 | 实际测试 |
| --- | --- |
| 认证 POST 不能误标交易 | K1真实 NEW 链；验证码GET/认证POST精确事件，交易POST=0，tokenGET=0；认证期写Cookie后失败清理；再调不重登 |
| 认证成功后交易才失败 | `test_auto_auth_then_trade_timeout_classifies_only_trade`，get/post/get/post，认证和交易各一次 |
| 已就绪交易不重发/补偿 | K2两交易；完整Session事件只有本次post，精确URL、allow_redirects=False、READY/token不失效 |
| HTTP/响应缺失/非整数 | create/cancel×400/503/307/308/201/-1；None/缺状态/getter/str/bool/float/不可信对象，字段不格式化 |
| 解码仍可能未知 | K3 JSON2/text与原JSON1/2/text计数；补bool/strip/缺json/text/日志handler抛错 |
| 正常业务不解释 | K4第二对象身份、Status=-1/list/None、rejected/空文本；P2 FalseResponse/None wrapper节点保留 |
| 前置失败无交易 | CLOSED/FAILED/无token/请求URL构造/post属性获取失败；输入strip失败；局部标记不跨调用污染 |
| 非交易语义 | 六查询HTTP/原Timeout身份；认证3阶段HTTP与失败清理；行情HTTP/原传输与decode；非法状态固定TypeError |
| 未知后只允许显式动作 | `test_explicit_query_after_unknown_is_not_automatic_recovery`，先验证零其它HTTP，再显式query一次，无login/token清理 |
| 锁包含解码与失败释放 | 新json2/text Event+ObservedLock原锁竞争；另一实例在释放前零HTTP，失败后只读查询完成，不靠sleep |
| 默认底层无自动重发 | 真实Session.request/send+纯内存adapter；307/308和Timeout各一次send；默认adapter总重试0、read=False、无auth/hook |
| 脱敏 | transport/JSON2/text/tradeHTTP/authHTTP/活跃except HTTP：原异常秘密、notes、嵌套cause不进入新异常标准显示；检查全部LogRecord字段 |
| 进程控制 | KeyboardInterrupt/SystemExit/GeneratorExit原对象传播、一次交易，不把无Unknown当未提交证明 |

`dist/p3-local/node-preservation.json` 实际对比JUnit：**350个P2基线(classname,name)全部存在于最终442项，未改nodeid，无skip/xfail/删除**。参数化中的原异常类型标签保留，仅在对应HTTP/交易分支精确切换预期，避免节点改名。

### 现有异常断言迁移（原节点 → 同名节点）

| 文件/函数 | 旧 → 新 | 保留的发送与状态断言 |
| --- | --- | --- |
| operations::test_uncertain_submission_never_replays_or_compensates | 原requests类型/身份 → 精确Unknown(exchange_error,None) | 2交易×3传输分支、事件1、post1/get0、READY/token |
| operations::test_order_bad_response_never_retries | AttributeError/RuntimeError → Unknown(exchange_error/http_status,500) | 2交易×None/HTTP、post1/get0 |
| operations::test_order_each_json_failure_propagates_without_retry | ValueError原对象 → Unknown(response_error) | JSON index1/2次数及post1 |
| operations::test_cancel_text_failure_propagates_once | ChunkedEncodingError原对象 → Unknown(response_error) | text1/post1 |
| operations::test_redirect_cannot_resend_order_at_adapter_level | 裸raise → Unknown(http_status,307/308) | 精确method/URL、adapter.send1 |
| operations::test_query_invalid_response_preserves_exception | 仅HTTP RuntimeError → BrokerHTTPError(503) | 六查询原参数、None/JSON原异常、post1 |
| operations::test_market_price_transport_and_decode_errors_are_not_nan | 仅HTTP RuntimeError → BrokerHTTPError(503) | 其它原类型/对象、get1 |
| auth::test_authentication_failure_invalidates_state_and_preserves_exception | 仅captcha/login/token_http RuntimeError → BrokerHTTPError(503) | 非HTTP原对象、token/Cookie清理、各阶段GET/POST次数 |
| logging::test_client_does_not_log_secrets_in_success_or_failure | 交易原异常 → Unknown；queryHTTP → BrokerHTTPError | 原完整LogRecord/repr检查、认证非HTTP原错误 |

旧API测试和tests/test_api_contract.py未改；旧普通/活跃except裸raise、同一异常对象重抛继续通过。另实际读取历史`dist/p1-repair/junit.xml`，其168个(classname,name)全部存在于最终442项，证据为`p1-node-preservation.json`。`final-scope-check.json`核对全部原测试文件字节，只有计划允许的4个新客户端测试文件改变；不通过数量增长宣称等价。

### 依赖侧静态审查范围

本机requests2.31.0 HTTPAdapter.send将默认`max_retries`交给urlopen，`redirect=False`。urllib3 2.8.0的Retry.increment在total=0时减至-1，is_exhausted触发MaxRetryError，先于urlopen递归；read=False直接重抛。已保存实际库源码和结论于`default-retry-review.json`。这结合配置测试与内存adapter证据支持SDK无自动重发，不伪称执行过真实HTTPAdapter网络路径或任意版本/自定义工厂均安全。

## 5. 变异反证（实际执行）

每个变异在**独立禁网进程**的pytest collection完成、P1 guard已安装后才替换内存生产函数，不修改生产文件。脚本先保存于`dist/p3-local/mutations.py`并实际执行，后按计划允许的测试证据归档到 [mutations.py](evidence/P3-local/mutations.py)。调整自动定位仓库根、增加main入口保护并统一格式；不加入生产设施或CI runner。

原实际命令为下式（依次取表中kind）；归档后复现将脚本路径替换为`docs/refactor/reports/evidence/P3-local/mutations.py`：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B dist/p3-local/mutations.py KIND
```

| kind/实际注入 | 目标选择 | 结果（全部退出1，collection errors=0） |
| --- | --- | --- |
| early：helper无条件包装前置异常 | trade_errors `-k test_k1` | 2 failed：认证Timeout错误变Unknown |
| remove：helper直接query+原解析，不转换 | trade_errors `-k test_k2` | 2 failed：原Timeout未转换 |
| post_only：只包query，不包解析 | trade_errors `-k test_k3` | 2 failed：JSON2/text原ValueError |
| replay：捕获Unknown后再调一次真实helper | trade_errors `-k test_k2` | 2 failed：完整事件有2次交易URL |
| query：捕获Unknown后调query_orders | trade_errors `-k test_k2` | 2 failed：完整事件出现额外查询URL |
| login：捕获Unknown后调login | trade_errors `-k test_k2` | 2 failed：额外验证码GET |
| redirect：强制disable_order_redirects=False | operations `-k test_redirect_cannot` | 4 failed：跟随第二次200响应，不再抛Unknown；不是无限redirect挂起 |
| implicit_context：去掉helper的from None | logging `-k test_new_errors_and_standard_traceback` | 4 failed/2 passed：标准显示秘密哨兵断言失败 |
| explicit_cause：helper改from error | 同上 | 4 failed/2 passed：标准显示秘密哨兵断言失败 |
| business：order_result复制dict返回 | trade_errors `-k test_k4_second` | 1 failed/2 passed：第二JSON对象身份改变 |

完整nodeid、调用参数、退出码和原日志：`dist/p3-local/mutation-KIND.{json,xml,log}`，汇总`mutations-summary.json`。对所有src/emtl与tests根Python文件的变异前后SHA256比较一致；恢复后的最终正常套件442项通过。预期变异失败不是最终正常测试失败。

归档脚本最终main入口/格式收口后再次实际执行全部10种变异，均退出1且有业务failure、无collection error，完整当前脚本SHA256与参数在`final-mutations-summary.json`，日志为`mutation-final-KIND.log`。随后正常trade_errors/logging集合通过，见`final-post-mutation-junit.xml`；46个代码/config文件哈希仍一致。

## 6. Linux 三入口及远端证据

Linux镜像按原Dockerfile实际准备完成，构建退出0（准备阶段允许网络，不执行真实账户测试）：

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p3-offline:local .
```

构建日志：`dist/p3-local/docker-build.log`。受测镜像为`sha256:64018ba142237b257f386e88d1b73ed5ceec3b521d31aa2526158b5be9c683bd`，平台linux/amd64。Docker daemon29.5.2。

实际命令（每条完整参数/cwd/退出码保存在`dist/p3-linux/host-commands.json`）：

```bash
docker create --name emtl-p3-cd48f8538439 --network none sha256:64018ba142237b257f386e88d1b73ed5ceec3b521d31aa2526158b5be9c683bd
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p3-cd48f8538439
docker start --attach emtl-p3-cd48f8538439
docker inspect --format '{{.State.ExitCode}}' emtl-p3-cd48f8538439
docker logs emtl-p3-cd48f8538439
docker cp emtl-p3-cd48f8538439:/workspace/dist/p1-offline/. dist/p3-linux/reports
docker rm -f emtl-p3-cd48f8538439
```

NetworkMode精确为none，容器退出0，start/logs/inspect/copy/cleanup均0。无宿主挂载或真实凭证注入；只删除本次创建的唯一容器。先收集全部报告再清理，失败状态不会被复制结果吞掉。

在另一个`--network none`短生命周期容器只读提取SHA256，确认镜像与最终macOS受测源码的**46个生产/测试/CI/config文件全部相同**（排除生成_version与缓存），`source-sha256.json`和`image-source-sha256.json`为实际清单。构建后的文档/测试证据脚本收口不属于此生产/测试清单，不声称整个文档树与镜像相同。

| 容器内步骤 | 实测结果 | 原始报告 |
| --- | --- | --- |
| 独立Linux OS探针 | 退出0，OS network namespace isolation verified | reports/command-00.log |
| 真实tox凭证隔离与默认完整入口 | 退出0；442 tests，JUnit时间29.460s；account environment isolated | reports/junit.xml、command-02.log、tox-result.json |
| 仓库外/tmp、不同文件顺序完整入口 | 退出0；442 tests，JUnit时间13.240s | reports/outside-junit.xml、command-03.log |
| 显式tests/完整入口 | 退出0；442 tests，JUnit时间15.231s | reports/explicit-junit.xml、command-04.log |
| 三份JUnit实际解析 | 节点集一致，各442项、0 failures/errors/skipped；350基线全部保留 | verification-summary.json |
| coverage | 行442/465、分支98/108，综合94.24% | reports/coverage.json、coverage.xml |

三轮不是1326个独立用例。容器沿用既有驱动，完整参数见`reports/commands.json`；路径仍名为p1-offline但数据属于本次P3镜像。tox父凭证由驱动构造为P1_FAKE_VALUE，`reports/synthetic-environment.json`可核实，执行期PIP_NO_INDEX=1。

Linux实际Python3.11.18、pytest9.2.0、pytest-cov7.1.0、coverage7.17.2、tox4.67.13来自`reports/versions.json`；另从同一镜像禁网读取requests2.31.0、urllib3 2.8.0，见`dist/p3-local/linux-http-versions.json`。Ruff/Black属于macOS检查，不冒称容器执行。

`dist/p3-linux`实际保存image/container inspect、逐命令日志、网络模式/退出码/宿主状态、全部三份JUnit/coverage/versions/commands/tox/合成环境与5份驱动步骤日志，SHA256索引为`evidence-sha256.json`。原始报告已导出，不是仅有控制台摘要。

远端最终提交的build与Offline tests、Artifact/head_sha/tree核对、独立新Session Review均**未执行**。不自动commit/push/PR/触发workflow。实施者diff自检不是独立Review。

## 7. 偏差、剩余风险与验收

- 没有设计/API范围偏差。按步骤先红灯、HTTP边界、再交易转换；S2用定向选择排除尚未接入转换的交易测试，最终无排除。变异脚本为计划§11允许的附带测试证据。
- 测试范围补充：post属性获取失败仍属前置；BaseException传播保留；特殊非200整数不猜测受理。没有新增订单业务校验、自动恢复或第三类异常。
- 脱敏只限SDK新异常的正常标准显示；from None不清内存context/frame，非HTTP认证/查询原异常仍可能带秘密，这是已批准的调试/兼容代价。
- 未知后READY保留、显式查询允许；调用方必须自行暂停自动化并人工核对。没有成交确认、幂等、跨进程或真实协议证据。
- 旧API的全局状态、失败保旧token、裸raise、默认重定向和缺timeout风险保留；工厂可信、无隐藏重发是P2前提。
- `dist/`均被Git忽略，是本机原始证据，不是已提交/上传Artifact；维护者交付前需保留或另行归档。独立Review及远端最终版本证据缺失时，**不得关闭P3或宣称最终PASS**。

最终交付自检实际覆盖tracked/staged/untracked：8个tracked修改、6个untracked交付文件，无staged内容；逐份检查新增异常、测试、契约、计划、报告及变异脚本。Ruff/Black检查含归档脚本共34个Python文件，均退出0；tracked/staged空白检查、Markdown围栏/相对链接、32份Linux原始证据SHA256复核通过，结果保存`dist/p3-local/final-quality-checks.json`。这只是实施者自检。

本地关键资金风险语义、旧API兼容、无自动重发、脱敏、锁行为与Linux系统禁网三入口已通过；最终验收还须独立Review PASS与远端双workflow/Artifact匹配最终提交树。完成后停止，不扩展P4。

## 8. 中断后续执行验证与任务进度

本轮按维护者要求保留已有实现，不重复修改生产代码或测试；实际新增修改仅为本报告与`docs/refactor/plans/P3-plan.md`的进度记录。原工作区8个tracked修改、6个untracked交付文件及HEAD保持原状，无staged改动。

重新核实：

- 当前HEAD仍为`ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`，46个代码/config文件SHA256与之前最终受测快照及Linux镜像清单一致。
- 32份Linux原始证据SHA256全部有效；重新解析三份JUnit，节点集一致，各442项且无失败/错误/跳过；P2的350节点与P1历史168节点全部保留。这是本轮证据复核，不冒称重新构建或重跑Linux。
- 10种变异的原实测非零退出码/业务失败证据有效；归档脚本SHA256与最终变异记录相同，不重复注入坏实现。
- 本轮重新运行完整macOS系统禁网套件，命令如下，退出0，**442 passed in10.33s**：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -vv --junitxml=dist/p3-local/resume-junit.xml
```

- Ruff/Black（包含归档变异脚本）重新运行均退出0，34个Python文件格式通过；未执行自动格式化或改写源码。
- 本轮证据索引：`dist/p3-local/resume-verification.json`、`resume-junit.xml`、`resume-tests.log`。原§3–6的基线/红绿/变异/tox/Linux原始记录不覆盖。

任务状态详见计划§20：**S0–S5已实现并验证；S6为PARTIAL，本地交付自检已完成，独立Review与最终提交远端双workflow/Artifact/Tree核对仍PENDING。** 不存在需重复开发的PARTIAL生产代码任务，也未发现新计划偏差。

下一步必须由新独立Review Session审查全部交付物；维护者控制提交/推送/PR后才能核对最终远端版本。继续Build的请求没有撤销禁止自动commit/push/发布的约束。本轮未进行这些操作、未调用真实账户或交易接口。

**总体验收仍为NEEDS EVIDENCE，不降低原计划条件、不关闭P3。** 未解决风险继续沿用§7；尤其原非HTTP异常可含敏感信息、Unknown不是重发许可，以及独立/远端证据尚未完成。

## 9. 首次独立Review FAIL与R1限定修复

### 9.1 审查与计划差异

维护者明确授权只读独立子会话Review。子会话`ses_e4a54104dffeFedISc2HJcgid3`输出**FAIL**，发现MEDIUM R1：HTTP200后的JSON或日志handler抛BrokerHTTPError时，原宽捕获误归为http_status并暴露该异常的状态字段，而非契约要求的response_error/None。完整事实与独立验证范围见[P3-review-R1.md](P3-review-R1.md)。此前442项绿灯未覆盖类型碰撞，不能作为已解决证明。

原计划§6.2的宽捕获伪代码与§5.1的阶段语义发生冲突。先在计划§22保存限定修正方案，以原公开契约为准：分开query与结果处理的捕获范围，不新增异常/字段、不改旧API、成功返回、锁或请求策略。这是为满足原契约的必要控制流调整，不是扩大P3范围。

### 9.2 实际改动与红绿证据

- `src/emtl/client.py::_execute_trade`：query阶段保留BrokerHTTPError特殊转换和前置失败原样传播；query正常返回后，全部普通响应处理异常统一为response_error/None。仍以局部attempted守卫、不捕获BaseException，外层账户锁及唯一POST保持。
- `tests/test_trade_errors.py::test_response_broker_http_error_is_not_exchange_http_status`：新增json1/json2/log/text四分支。log用真实logging.Handler；底层合成Session返回HTTP200；JSON/text属性只替换响应依赖，不Mock公共包装。检查精确Unknown字段、原响应200、解析次数、POST1/get0及READY/token不变。
- P3契约补充阶段优先解释。无其它生产/测试修改；与首轮受审46文件哈希相比，仅上述client和trade_errors变化，见`dist/p3-r1/source-delta.json`。

先在未修复代码执行新增回归：退出1，**4 failed**，均因actual=http_status、expected=response_error，0 collection errors。原日志`dist/p3-r1-red.log`、JUnit`dist/p3-r1/red-junit.xml`，不是导入/语法错误假红。

修复后以同一sandbox前缀运行trade_errors、client_operations、client_logging、client_concurrency，退出0，**219 passed**，JUnit/日志为`dist/p3-r1/targeted-junit.xml`、`targeted.log`。完整命令沿用§3系统禁网前缀；选择与结果如下：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_trade_errors.py -k response_broker_http_error -vv --junitxml=dist/p3-r1/red-junit.xml
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_trade_errors.py tests/test_client_operations.py tests/test_client_logging.py tests/test_client_concurrency.py -vv --junitxml=dist/p3-r1/targeted-junit.xml
```

真实sandbox tox（合成父环境、PIP_NO_INDEX=1、TOXPYTHON同§3）退出0，**446 tests，0 failures/errors/skipped**；完整参数/环境/退出码和日志在`dist/p3-r1/tox-command.json`、`tox-result.json`、`tox.log`，最终JUnit/coverage亦在该目录。原P2的350、P1的168及首轮P3的442节点全部保留，不改旧nodeid或断言。JUnit时间32.369s。覆盖率仅观察：行444/468，分支99/110，综合93.94%；不因覆盖率变化扩展工作。

10种既有变异全部在独立sandbox进程复跑，仍全部退出1且由业务failure检出、无collection error。为保留首轮原件，用归档脚本的只读导入入口注入内存变异，输出新路径`dist/p3-r1/mutation-KIND.{xml,log}`，原dist/p3-local证据未覆盖。实际完整子进程代码/参数/退出码为`mutations-summary.json`，逐项解析与哈希不变结果为`local-verification.json`。

Ruff/Black（含归档脚本）通过，未改变工具规则。修复后Linux最终镜像按原Dockerfile重建中，构建日志与实际结果将保存在`dist/p3-r1/docker-build.log`、`docker-build-result.json`。首轮§6镜像已不等于修复后代码，**不能用它签认最终验收**；必须取得新Linux证据与独立复审后更新本节。

### 9.3 Linux镜像准备失败与替代安排

上述原Dockerfile重建已实际退出**2**，原因是准备阶段pip下载virtualenv时files.pythonhosted.org读取超时；没有执行交易测试。失败原始日志与命令/退出码完整保留，不覆盖、不冒称成功。

已先在计划§22.1记录偏差分析：依赖/config不变，复用首轮已准备的固定镜像，仅禁网COPY最终src/tests/docs；必须证明基础RootFS层前缀和46文件哈希一致后再运行原Linux验收驱动。不会修改已提交Dockerfile、依赖或CI，不增加测试联网权限。最终实际结果在下方追加。

薄层构建实际退出**0**，镜像`sha256:b01c9f2ffbcb08826e5d99be4311bbb5bfc3dbc1ec84e390867199afa9f69dfd`。最终18层的前15层与准备镜像RootFS完整一致；完整stdin/参数/退出码、新旧inspect及层关系为`dist/p3-r1/docker-build-final-result.json`、`docker-build-final.log`、`prepared-image.json`、`final-image.json`、`image-lineage.json`。此构建没有下载依赖；原下载失败记录仍保留。最终Linux运行与独立复审尚待完成，不能仅凭镜像成功关闭R1。

### 9.4 R1修复后最终Linux系统禁网结果

最终受测镜像为上述`b01c9f2f...`，linux/amd64。先在独立--network none容器只读提取46文件哈希及HTTP依赖版本，实查与当前R1受测源码/config一致，非复用首轮旧源码。随后以唯一容器`emtl-p3-r1-bbb30e40b3e4`运行既有驱动，无宿主挂载/真实凭证注入；NetworkMode精确none，容器退出0，start/logs/inspect/copy/cleanup全部0，先完整导出报告后仅删除本次容器。

实际宿主命令及退出码见`dist/p3-r1-linux/host-commands.json`；关键命令如下：

```bash
docker create --name emtl-p3-r1-bbb30e40b3e4 --network none sha256:b01c9f2ffbcb08826e5d99be4311bbb5bfc3dbc1ec84e390867199afa9f69dfd
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p3-r1-bbb30e40b3e4
docker start --attach emtl-p3-r1-bbb30e40b3e4
docker inspect --format '{{.State.ExitCode}}' emtl-p3-r1-bbb30e40b3e4
docker logs emtl-p3-r1-bbb30e40b3e4
docker cp emtl-p3-r1-bbb30e40b3e4:/workspace/dist/p1-offline/. dist/p3-r1-linux/reports
docker rm -f emtl-p3-r1-bbb30e40b3e4
```

| 原驱动步骤 | 结果 | 原始证据（相对dist/p3-r1-linux） |
| --- | --- | --- |
| 独立OS探针 | 退出0，OS network namespace isolation verified | reports/command-00.log |
| 真实tox前置合成凭证隔离 | 退出0，account environment isolated | reports/command-02.log、tox-result.json |
| 默认完整入口 | 446项，0失败/错误/跳过，JUnit时间24.158s | reports/junit.xml |
| 仓库外不同顺序 | 446项，0失败/错误/跳过，JUnit时间8.663s | reports/outside-junit.xml |
| 显式tests入口 | 446项，0失败/错误/跳过，JUnit时间16.169s | reports/explicit-junit.xml |

三份JUnit节点集一致，原P2的350、P1的168及修复前P3的442节点全部保留；不是累计1338个独立测试。Coverage行444/468、分支99/110、综合93.94%，与macOS相符，仅作观察。

实查LinuxPython3.11.18、pytest9.2.0、pytest-cov7.1.0、coverage7.17.2、tox4.67.13（reports/versions.json）；requests2.31.0、urllib3 2.8.0（http-versions.json），依赖准备层未改变。完整命令/工作目录/退出码、三份JUnit/coverage/XML/JSON/合成父环境/日志、image/container inspect、宿主状态、源码与证据哈希都已实际导出，见该目录verification-summary.json与evidence-sha256.json。dist仍为被Git忽略的本机证据，不冒称远端Artifact。

R1的Build修复与最终本地验证已完成，等待原独立审查子会话复审；首次FAIL仍保留，Build不能自行签认关闭R1，远端最终版本证据仍待维护者控制交付。

## 10. R1独立复审完成及最终本地交付状态

原独立审查子会话`ses_e4a54104dffeFedISc2HJcgid3`实际完成只读复审：**R1已关闭（仅当前受审快照）；源码/本地独立Review PASS；P3总体NEEDS EVIDENCE**。完整独立结论归档[P3-review-R1-followup.md](P3-review-R1-followup.md)，首次[P3-review-R1.md](P3-review-R1.md)的FAIL保留，不倒改历史。

独立复审实际重新执行完整sandbox套件两次：446 passed（10.03s、7.60s）；原真实handler反例正确分类response_error/None；内存恢复首轮宽捕获后新增四测试均因字段断言失败；原10种变异也均被业务失败检出，无collection/setup/teardown错误。Ruff与tracked/staged diff检查通过。独立确认当前46文件与新镜像哈希相同，最终Linux33份证据及首轮32份证据哈希有效，三入口节点集一致且原350/442/168节点完整保留，容器禁网/退出/真实tox隔离证据有效。未发现其它确定缺陷。

审查未修改任何项目或原证据文件，未访问网络/真实账户/券商/OCR，未触发CI；未重新执行Docker/tox/Black，此部分是原始记录独立核验，不冒称全部重新运行。

当前任务状态：S0–S5及R1修复/最终本地验证**COMPLETED**；S6独立Review **COMPLETED**；S6远端交付核验 **PENDING**。没有未验证的生产代码IMPLEMENTED项、未完成的代码PARTIAL项或结果UNKNOWN项。归档后源码不再修改；维护者仍需控制提交/推送/PR，并核对最终head_sha的build与Offline tests、Artifact、NetworkMode、容器退出、三份JUnit及合并Tree。

本轮R1相关修改限于`src/emtl/client.py`、`tests/test_trade_errors.py`、P3契约、计划、本文及两份独立Review归档。原阶段完整文件清单仍见§2。仅验证准备从原Dockerfile联网下载失败转为已准备依赖镜像上的禁网COPY薄层，偏差、失败和成功证据均保留，不改变CI/config、运行时依赖或验收标准。

**尚不关闭P3。** dist/p3-r1与dist/p3-r1-linux为本机被忽略证据，维护者应保留；远端原CI构建及最终版本证据不可用本地薄层验证替代。没有commit/push/发布或真实交易。

复审归档后最终自检：当前8个tracked修改、8个untracked交付文件、无staged；Ruff/Black及tracked/staged空白检查通过，新增文档围栏/相对链接有效，代码/config46文件哈希未变；最终Linux33份及旧Linux32份证据哈希完整，四份完整JUnit（本地+Linux三入口）446节点一致。机器记录为`dist/p3-r1/final-quality-checks.json`；此归档自检不改变独立Review的受审代码快照或结论。

## 11. 第二轮Review FAIL（R2）：交易HTTP状态来源定向修复

### 11.1 Review事实、范围和修复前状态

维护者本次明确要求仅修复HTTP状态来源，不重新设计P3异常体系。维护者提供的Review FAIL包括：

1. session.post抛BrokerHTTPError(401)，旧实现误归http_status/401，契约应为exchange_error/None。
2. Response.status_code getter抛BrokerHTTPError(401)，旧实现同样误归http_status/401，应为exchange_error/None。
3. 实际Response状态503，但日志handler抛BrokerHTTPError(401)，旧实现错误使用401覆盖503。

实查`client.py:97–103`、`204–207`与描述一致，无需推测。先保存计划§24，再写真实公共链失败回归；R1修复及复审PASS仍保留为当时历史，未改写任何原Review FAIL或独立意见。

本次新增/修改范围：

| 文件 | 本次修改 |
| --- | --- |
| `src/emtl/client.py` | 仅本次调用的已验证HTTP来源通知/分类，不再读取捕获异常的类型、属性或消息推断状态 |
| `tests/test_trade_errors.py` | 三场景×两交易的6项回归；另两项读取一次/后续调用不污染测试 |
| `docs/refactor/reports/evidence/P3-r2/http_source_mutations.py` | 两个独立禁网进程的来源判断定向内存变异脚本 |
| `docs/refactor/plans/P3-plan.md`、本文 | 先行限定修复计划、历史保留、实测/偏差/剩余风险 |

与R1最终46文件哈希比较，生产/测试/config只有client.py与test_trade_errors.py改变（`dist/p3-r2/source-delta.json`）。旧core、_protocol、errors、__init__、账户协调、CLI、端点/表单、依赖、隔离设施、Docker与CI均未改；未新增异常/分类/全局状态机、自动交易恢复或重试。

### 11.2 来源信号实现

- `_check_resp`只从本次传入的Response读取status_code一次，先进行精确int检查。仅成功读取且验证为非200后，才通过私有可选回调记录该值，发生在调用任何日志handler之前。getter失败/非法值均不建立HTTP来源。
- `_query_something`在两项交易使用本次局部check闭包转发通知；认证仍在前，验证码/登录/token GET不使用交易观察，查询/行情默认路径不变。
- `_execute_trade`使用每次调用独立的`http_status=None`及赋值闭包，不保存self/global共享字段。query异常只根据这项真实Response证据分类：已验证非200为http_status/该值，否则exchange_error/None，绝不从异常本身取状态。
- R1结果处理捕获范围保持：query正常返回后JSON/text/真值/订单日志等普通异常仍response_error/None；BaseException、前置失败、外层账户锁、一次POST、READY/token策略与原成功返回不变。

### 11.3 先红后绿与完整离线验证

`test_trade_http_status_requires_response_source`参数化post/status_getter/http_log × create_order/cancel_order，真实执行TradingClient公共链，只替换底层合成Session/Response/真实logging.Handler；没有Mock被测分类函数。

每项先断言业务POST恰好1次、GET0次、完整Session事件只有该交易、allow_redirects=False、READY/token与Cookie保持；检查状态getter调用数、无JSON解析、精确Unknown字段，使用`assert_no_sensitive_logs`覆盖SDK LogRecord的msg/args/getMessage/exc_info/exc_text/stack_info，哨兵包括合成账号、密码、token、Cookie、Authorization、请求/响应体和原异常note。

修复前执行：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_trade_errors.py -k trade_http_status_requires_response_source -vv --junitxml=dist/p3-r2/red-junit.xml
```

真实退出1，**6 failed，0 errors/skipped**；前四项因http_status≠exchange_error失败，后两项因401≠503失败。原日志`dist/p3-r2-red.log`保留，不是导入/语法错误假红。

修复后交易/认证/业务/日志/并发集合退出0，**265 passed**（早于后加的两项读取一次/不粘滞测试），见`dist/p3-r2/targeted-junit.xml`、`targeted.log`。新增`test_trade_status_is_read_once_and_does_not_leak_to_next_call`两交易分支证明首次真实503仅读取一次，下一次post异常401回到exchange_error/None，无上次状态污染；既有非法status矩阵继续通过。

最终完整pytest和真实tox分开执行，均加同一系统sandbox/禁字节码/禁缓存，退出0，**各454 tests，0 failures/errors/skipped**：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -vv --junitxml=dist/p3-r2/pytest-junit.xml
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p3-r2/tox-result.json -- python -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-report=xml:dist/p3-r2/coverage.xml --cov-report=json:dist/p3-r2/coverage.json --junitxml=dist/p3-r2/tox-junit.xml -vv
```

完整实际参数/cwd/退出码为`pytest-command.json`、`tox-command.json`；后者同时记录明确合成父环境（P3_R2_FAKE_VALUE，EM_*与凭证隔离哨兵）、PIP_NO_INDEX=1、TOXPYTHON和禁字节码设置，日志为`pytest.log`、`tox.log`。真实tox隔离前置检查输出account environment isolated。两份JUnit时间分别15.494s、17.301s，节点集一致，原P2的350、P1的168及修复前P3的442/446节点全部保留，无删改/skip弱化。

本机版本另存`dist/p3-r2/versions.json`。coverage仅作观察：行452/475，分支104/114，综合94.40%，不作为分类正确的替代证明。

### 11.4 定向来源变异与恢复验证

归档新脚本[http_source_mutations.py](evidence/P3-r2/http_source_mutations.py)只在pytest collection完成、P1 guard已安装后的独立sandbox进程内替换生产函数；正常回归不Mock分类函数，不改磁盘源码：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B docs/refactor/reports/evidence/P3-r2/http_source_mutations.py exception_source
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B docs/refactor/reports/evidence/P3-r2/http_source_mutations.py late_source
```

| 变异 | 实际检出 |
| --- | --- |
| exception_source：去掉真实来源判断，改按BrokerHTTPError类型及error.status_code推断 | 退出1，6项精确字段失败；原401伪状态重新出现 |
| late_source：将真实状态通知移到日志handler之后 | 退出1，2项实际503+handler401回归失败（错误变exchange_error） |

两者均无collection error；执行参数/退出码、JUnit和完整日志在`dist/p3-r2/mutation-KIND.{json,xml,log}`。另将原归档10种变异通过只读runpy入口在新目录复跑，全部由业务失败检出，未覆盖旧报告。`mutations-summary.json`保存12种完整命令、注入代码、真实退出码/失败数及新脚本哈希；最终46代码/config哈希不变。

变异后在正常新进程重跑R2来源/不粘滞与R1阶段分类集合，12项通过，见`post-mutation-junit.xml`、`post-mutation.log`，证实无变异残留。

### 11.5 静态检查、剩余风险和验收边界

Ruff、Black（含两个归档变异脚本）及git diff --check实际运行；初次Black指出新增测试排版，已仅调整新增片段，最终35个Python文件检查通过，没有改变项目规则。

本次按维护者限定完成来源识别修复及指定本地验证，没有扩大生产范围或改变P3公开异常契约。仅增加了两项来源局部性回归与测试专用定向变异脚本。没有真实交易、真实账户、自动重试/补偿/确认或commit/push/merge。

**旧Linux镜像及446项Linux证据不适用于修复后的R2源码。** 本轮没有重建/运行R2 Linux镜像或取得新的独立复审/远端最终提交证据，不把旧PASS改称为新PASS；第二轮Review FAIL仍须独立复审关闭，P3不能最终验收或关闭。原非HTTP异常/内存context/APM安全边界、可信工厂限制与Unknown不得自动重发的风险继续保留。dist/p3-r2是本机被忽略证据，应由维护者保留。

最终交付检查记录`dist/p3-r2/final-checks.json`：Ruff/Black/diff均退出0、文档链接和围栏有效、源码/config哈希无变异残留、相对R1仅指定两个代码/测试文件变化、两轮旧Linux证据哈希保留且明确不适用于R2；staged为空。实施者静态复核确认_execute_trade不读取任何异常status_code，也不再按BrokerHTTPError类型分支；该自检不代签独立Review。

## 12. 第三轮定向修复R3：非交易HTTP错误受日志Handler覆盖

### 12.1 原Review FAIL与限定改动

维护者提供当前Review FAIL：查询、行情、登录验证码实际返回503时，真实logging.Handler抛BrokerHTTPError(401)或ValueError，调用方可能收到Handler原异常，其合成message、exception notes/cause/context可能进入标准traceback。要求只修复已确认HTTP错误的日志覆盖，BaseException原样传播，旧core及R2交易来源逻辑不得改变。

实查client._check_resp与描述一致。先在计划§25保存限定方案，再补测试、执行失败证据、最后改实现。本次不改写既有FAIL或R1/R2历史结论。

| 文件 | 本次改动 |
| --- | --- |
| `src/emtl/client.py::_check_resp` | 已验证非200时先构造安全HTTP异常；仅捕获logger.error的Exception；最后raise安全异常from None |
| `tests/test_client_logging.py` | 新增6项真实链安全回归、3项BaseException传播、1项构造时序、3项旧core原行为回归及小型依赖布置/请求断言帮助函数 |
| `docs/refactor/reports/evidence/P3-r3/http_logging_mutations.py` | 5种指定错误实现及1项R2来源时序的独立禁网内存变异 |
| `docs/refactor/plans/P3-plan.md`、本文 | 先行计划与实际红绿/变异/完整回归、剩余边界追加 |

与R2最终46文件哈希比较，只改变client.py和test_client_logging.py，见`dist/p3-r3/source-delta.json`；将_check_resp限定片段在内存还原后，完整client.py哈希与R2一致，证明_query_something/_execute_trade等R2方法字节不变。移除新增imports和文件末尾R3用例后，原logging测试文件哈希也与R2一致，无弱化旧断言。

core.py、_protocol.py、errors.py、账户协调、包级导出、CLI、依赖/config/CI均未修改。没有新增异常类/字段/框架、自动重试、交易POST、补单/撤单/确认或P4工作。

### 12.2 安全HTTP错误和Handler边界

_check_resp仍先从本次Response读取status_code并做原精确int验证。只有读取/验证成功且非200才构造`BrokerHTTPError(status)`，沿用公开`status_code`字段表达HTTP状态，不新增http_status别名。

安全异常建立后，原R2的本次局部状态通知仍发生在日志之前；随后仅将固定logger.error调用放入try/except Exception。Handler普通异常不再覆盖真实HTTP错误，不格式化/复制其message、notes或cause，不增加其它错误日志；最后显式raise预先建立的安全异常from None。

不捕获BaseException，不用finally强制HTTP错误取代进程控制异常。Handler的自定义BaseException仍原对象传播；登录原finally仍清认证态/Cookie。R2交易来源仍由局部已验证状态决定，未读取Handler异常类型/属性推断HTTP状态。

此安全保证针对SDK新HTTP异常和默认不显示locals的标准traceback；不清除内存frames/context或控制宿主APM/自定义格式器。屏蔽普通Handler故障细节是明确的诊断代价；没有扩大到非HTTP原异常或旧core日志行为。

### 12.3 先行失败和真实公开链回归

`test_non_trade_http_error_survives_handler_failure`覆盖验证码/查询/行情 × BrokerHTTPError(401)/ValueError共6场景，真实执行TradingClient公共链，底层仅合成Session/Response与真实logging.Handler。原Handler异常携带合成message、note和嵌套cause；BrokerHTTPError(401)也设置独立合成args以验证其消息不能进入新异常。

每项断言最终精确BrokerHTTPError/status_code503、新对象而非原Handler错误、无复制notes、cause=None及suppress_context=True，str/repr/args/字段和标准traceback无哨兵。实际Handler接收的完整LogRecord与caplog记录一起检查（不因Handler中断传播导致caplog为空而得到假绿），固定日志必须恰好一次、msg/args为request failed/code503。

请求及状态断言：查询业务POST1/GET0；行情与验证码GET1/POST0，精确URL或验证码前缀/timeout60；无JSON解析、无close/OCR或额外认证请求；Session身份不变。查询/行情保留READY/token/Cookie；显式登录验证码失败仍FAILED、空token、Cookie清空。

修复前实际执行：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_client_logging.py -k non_trade_http_error_survives_handler_failure -vv --junitxml=dist/p3-r3/red-junit.xml
```

真实退出1，**6 failed，0 errors/skipped**。3项Broker错误因401≠503失败；3项ValueError原消息/notes传播而非安全HTTP错误。原日志`dist/p3-r3-red.log`及red-junit.xml保留，非语法/导入错误假红。

修复后初次交易/认证/业务/日志/并发集合**280 passed**（`targeted-junit.xml`、`targeted.log`）。之后只强化新增用例的实际LogRecord检查并修正格式，最终快照另由完整467项及变异后124项验证，不把中间测试快照冒称最终原件。

另外：

- `test_non_trade_http_handler_base_exception_propagates`三路径断言同一自定义BaseException传播、无额外HTTP和原生命周期行为。
- `test_safe_http_error_is_established_before_logging`单独观察异常构造事件与真实Handler日志事件，要求error503→log503。观察器返回真实BrokerHTTPError，只观察构造，不Mock分类函数、不替代上述6项真实链回归。
- `test_legacy_core_http_handler_failure_remains_original`通过旧core.query_orders分别验证BrokerHTTPError(401)/ValueError/自定义BaseException继续原对象传播，旧token/Session与单次POST不变；旧裸raise/活跃except和CLI另由原套件覆盖。

### 12.4 指定Kill/Mutation实际结果

新脚本[http_logging_mutations.py](evidence/P3-r3/http_logging_mutations.py)仅在pytest collection后、P1 guard已安装的独立sandbox进程内变异_check_resp的AST，不修改磁盘源码。使用真实模块globals保持构造观察器接缝，避免因复制globals破坏观察器而假红。每个变异实际命令为：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B docs/refactor/reports/evidence/P3-r3/http_logging_mutations.py KIND
```

| KIND / 注入错误 | 实际检出（均退出1、0 collection errors） |
| --- | --- |
| late_error：保留其它保护，仅将安全异常建立移到日志之后 | 1项构造时序失败，实际log→error，非观察器失效 |
| reraise_handler：捕获后裸raise Handler原异常 | 6项类型/401字段或原异常传播失败 |
| handler_cause：raise安全HTTP异常from Handler原异常 | 6项标准traceback秘密哨兵检查失败 |
| handler_message：将Handler消息拼入安全异常args | 6项异常显示秘密哨兵检查失败 |
| swallow_base：将日志guard改捕获BaseException并吞掉 | 3项原自定义BaseException传播检查失败 |
| late_status：将R2状态通知移入日志调用之后 | R2实际503+Handler401的2项来源回归失败，证明来源先后关系仍受保护 |

完整参数/真实退出码/失败数和脚本哈希为`dist/p3-r3/mutations-summary.json`；每种另有mutation-KIND.json/xml/log。没有以语法、collection、setup或teardown错误冒充检出。原R2文本变异脚本针对当时快照，保留不改；本轮使用新的AST变异验证当前结构，不拿旧脚本的文本匹配失败当证据。

变异后正常新进程运行client_logging与trade_errors，**124 passed**，见`post-mutation-junit.xml`、`post-mutation.log`。全部46文件哈希保持当前受测快照，无变异残留。

### 12.5 最终完整禁网pytest/tox与原P0/P1/P2保护

最终当前快照两种完整入口分别执行，均退出0，**各467 tests，0 failures/errors/skipped**：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -vv --junitxml=dist/p3-r3/final-pytest-junit.xml
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p3-r3/final-tox-result.json -- python -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-report=xml:dist/p3-r3/final-coverage.xml --cov-report=json:dist/p3-r3/final-coverage.json --junitxml=dist/p3-r3/final-tox-junit.xml -vv
```

实际参数/cwd/退出码分别保存final-pytest-command.json、final-tox-command.json，日志为final-pytest.log、final-tox.log；tox父环境只覆盖固定P3_R3_FAKE_VALUE合成账户/凭证隔离哨兵，设置PIP_NO_INDEX=1、TOXPYTHON与禁字节码，真实commands_pre在pytest前输出account environment isolated。JUnit时间分别13.142s、8.755s，完整节点集合一致。

独立解析原P1历史168、P2基线350及R2最终454节点，全部存在于当前467项，无删改节点、skip或弱化旧断言；R2交易来源6项及读取一次/局部状态测试持续通过，旧API/CLI、认证/账户隔离与订单不重发原回归均通过。源码/节点/coverage核验摘要为`dist/p3-r3/verification-summary.json`。

本机实际版本为Python3.11.14、pytest9.2.0、pytest-cov7.1.0、coverage7.17.2、tox4.67.12、requests2.31.0、urllib3 2.8.0，另存versions.json。覆盖率仅观察：行456/479、分支104/114、综合94.44%，不是通过依据。

Ruff/Black（含三份变异脚本）与git diff --check实际执行。初次检查指出新增测试排版/合成token命名及脚本断言风格；仅修新增片段，未改规则，最终36个Python文件检查通过。

### 12.6 状态、剩余风险及停止

R3本地定向修复与指定检查完成；**Review仍等待独立复审，不自签PASS、不改写原FAIL、不关闭P3**。本轮没有独立审查、没有新Linux镜像/运行或远端最终版本核验，旧446项Linux证据和旧PASS不得用于当前快照。

仅普通日志Handler的故障被已确认安全HTTP错误取代；BaseException有意原样传播，非HTTP原异常/内存context/APM边界不扩张，Unknown仍不是重发许可。全程合成账户、禁网、无真实交易，没有新增自动重试/POST/补偿/确认，没有commit/push/merge或P4改动。所有新证据在被Git忽略的dist/p3-r3，应保留。依维护者要求，归档后停止，等待独立Review。

最终交付自检为`dist/p3-r3/final-checks.json`：Ruff/Black/diff退出0，文档围栏/相对链接有效；受测46文件无变异残留，R2生产方法与原logging断言字节保留，logger guard只捕获Exception；旧Linux原始证据哈希保留且明确不签认R3，staged为空。此为实施者一致性检查，不代替独立Review。

## 13. F1/E1最终交付限定修复（2026-11-08）

### 13.1 输入、范围和中断恢复

维护者确认交易生产及R1–R3功能Review通过，但当前交付Review为FAIL，要求先关闭F1再执行E1。本轮不改交易生产代码、测试、CI、依赖或异常行为，不扩大P4，不自动commit/push/merge。完整限定计划先保存在P3-plan.md §26；中断恢复后只继续未完成项，不重复开发或重做迁移。

F1检查的verify_host.py/observe.py实际绑定本机ROOT、/workspace、单次run及467节点，是一次性证据脚本；原计划§11允许附带证据，但没有强制这两个临时脚本入库。它们已原字节迁到Git忽略的dist/p3-f1e1/tools/original，原/新路径及SHA256见[script-relocation.json](evidence/P3-final-linux/script-relocation.json)，没有为了lint批量noqa或改配置。

同时发现旧P3构建仍在运行并会继续写待整理目录。维护者明确选择“停止旧构建并继续”后，仅停止经PID/命令/tag识别的旧进程及其构建容器，未删除源码、日志或镜像；操作原件为dist/p3-f1e1/f1/old-build-stop.json/log，关联记录亦保存在script-relocation.json。此中止不算E1或功能测试结果。

整理前25份原始材料（包含原README、manifest、本地JUnit、Git/失败及部分构建日志）保留原字节于[history-before-f1.tar.gz](evidence/P3-final-linux/history-before-f1.tar.gz)；[history-files-sha256.json](evidence/P3-final-linux/history-files-sha256.json)记录归档与成员哈希，实际逐项核验一致。单份原件保存在忽略的dist目录，不把临时日志散落为待提交文件，也不通过改原始日志空白/换行凑hooks通过。历史README中的未生成材料已在当前[索引](evidence/P3-final-linux/README.md)澄清；原README仍在归档内。

中断恢复核对：46个源码/测试/config文件仍与R3最终快照一致；脚本迁移和原始归档完整。F1尚待完整候选树质量门槛，E1未启动；以下节只记录随后实际运行的结果，不提前声明通过。

### 13.2 F1关闭

完整候选树共103文件，含全部untracked交付文件。第一次隔离检查失败仅因临时工具用copyfile丢失ci/bootstrap.py与setup.py的可执行位，触发Ruff EXE001；未改真实文件或规则，失败日志保留在dist/p3-f1e1/f1/f1-complete-tree。改用copy2保留原权限后，dist/p3-f1e1/f1/f1-preserve-modes/result.json记录PASS：隔离完整树与真实工作区pre-commit run --all-files全部通过；11个待交付Python文件直接Ruff/Black检查通过；unstaged/staged diff检查通过，真实index和所有候选原字节不变。46文件R3保护哈希一致。F1于此关闭，后续才启动E1。

初始候选及历史归档扫描共103文件、25归档成员，没有私钥/带密码URL/凭证文件名命中；此项为限定模式扫描，不等同于穷尽秘密检测，最终交付仍需检查新证据。E1状态待后续实际结果追加。

### 13.3 新E1实测结果及原始交付证据

在F1关闭后重新锁定完整工作区和467节点基线，原Dockerfile、当前完整context、--no-cache构建成功，未用旧镜像或COPY薄层替代。镜像为linux/amd64，ID `sha256:2150b9bc9fe31e0785163731ccd487853810ed6c33411d5769d2ab6983e05a9b`，唯一tag `emtl-p3-final-linux:197eec73af7d`。源码/全部tests及fixtures、CI/config和文档共95项COPY输入在容器测试前后与宿主锁定SHA256一致；R3保护的46文件仍一致。归档内input-audit-clarification.json澄清继承旧host脚本的描述标签，本轮5份历史目录文件实际均在95项中，无遗漏。

| 原批准入口 | 完整JUnit | 结果 | JUnit累计时间 |
| --- | --- | --- | --- |
| tox根默认收集入口，原coverage参数 | e1/reports/junit.xml | 467 passed；0 failure/error/skip | 53.745秒 |
| /tmp仓库外、指定不同文件顺序 | e1/reports/outside-junit.xml | 467 passed；0 failure/error/skip | 19.818秒 |
| 仓库内显式tests/ | e1/reports/explicit-junit.xml | 467 passed；0 failure/error/skip | 12.690秒 |

三份节点完全等于锁定本地467节点集合，无重复，无靠改测试凑数。唯一容器NetworkMode=none，无宿主挂载或真实凭证注入；7次系统OS探针均通过，包含每入口前后，原tox commands_pre在pytest启动前输出account environment isolated。Python 3.11.18、tox 4.67.13、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2；coverage JSON/XML完整保存，综合94.44%、语句95.20%、分支91.23%。三入口共享一个禁网容器，并不是1401个独立测试或三次容器启动。

宿主构建、create/copy/start/logs/inspect/报告导出/cleanup命令均退出0；容器实际退出0，停止且确认本次唯一容器清理后不存在。镜像保留、无push/publish；RepoDigests仅是daemon元数据，不冒称registry交付。原件在dist/p3-f1e1/e1，封存交付在[新证据索引](evidence/P3-f1e1/README.md)：raw-evidence.tar.gz含122份F1/E1实际原件（完整日志/JUnit/coverage/tox/版本/隔离/manifest/image/network/退出/清理/宿主命令）；raw-files-sha256.json覆盖每份成员及归档，SHA256SUMS覆盖归档和成员索引，已重新打开归档逐项核验。隔离候选树可重建副本及.git不入归档，原始命令日志无排除；临时Python操作工具原字节作审计附件封装，不作为正式工具新增到源码树。

历史446 Linux、旧本地467及旧最终Linux尝试都不是这轮结果；旧Review FAIL及旧原始材料原字节保留。受测实现未变，测试后只会更新验收/索引/证据封装，不声称最终文档与测试镜像字节一致。本轮不代签独立Review，最终远端PR提交、head_sha、双工作流/Artifact/Tree仍待维护者受控交付后核验。

### 13.4 最终交付复核及停止

原件封装和索引更新后再次执行dist/p3-f1e1/tools/check_quality.py final-delivery：108个完整候选文件（所有tracked及untracked）在独立index的隔离树中执行原pre-commit run --all-files通过，真实工作区同命令通过；全部11个待交付Python的Ruff/Black、unstaged/staged diff检查通过，候选文件字节与真实index未被hooks改写。最终补充封装和本节收尾后，使用同一门槛再次复核完整清单，不通过则仍视为交付阻断。

静态扫描覆盖108个候选文件及147个归档成员（包括旧25份原件和新122份原件），没有私钥/凭证URL/GitHub token/AWS access ID/凭证文件名命中；7个非空credential-like Python字面量均核验为明确的合成/fake测试哨兵，生产及普通工具无此类候选。未读取或输出真实账户环境；模式扫描不是穷尽未知秘密检测。变更Markdown相对链接20项检查无缺失。源码对应核验再次证明46文件保护快照不变，原COPY清单只有测试后追加的验收文档不同，未修改生产/测试/CI/依赖/config。

最终建议提交清单见[delivery-inventory.json](evidence/P3-f1e1/delivery-inventory.json)：包含原有8个tracked修改及新增交付文件，所有其他文件有SHA256；inventory自身避免自引用不填自哈希。dist中的临时工具/环境/缓存/原始散落日志及候选树不提交；审计所需原件只封装为带索引归档。补充delivery-checks.tar.gz保留封存后质量检查、秘密模式扫描、链接/来源验证记录与最后交付工具审计副本；该补充检查快照早于本段收尾文档，不冒称自包含最终文档哈希。归档/成员索引仍逐项验证，最后完整清单再跑质量门槛；真实staging保持为空。

本轮停止条件已取得实际依据：F1关闭；原Dockerfile新Linux镜像三入口均467通过；源码/镜像前后哈希/原始报告/归档SHA256链路成立；建议提交清单明确且无dist临时产物。尚缺的是维护者控制的最终Git提交/PR、匹配head_sha的双远端CI、Artifact和Tree证据，以及人工独立签认；这些不由本地结果或本实施者签认替代。没有自动commit/push/merge/tag，没有进入P4或改变交易行为。

收尾实测：dist/p3-f1e1/f1/final-closure/result.json为PASS，完整109文件候选树及真实工作区pre-commit通过、11个交付Python Ruff/Black与diff通过，真实index/候选字节未变化。补充归档后静态扫描覆盖109文件、173归档成员，零命中。最终建议提交29文件（8个tracked修改、21个untracked新增，包含本清单自身）；清单涵盖原有P3实现，不表示本轮重新修改了这些源码。本段记录及inventory哈希刷新后再运行相同质量门槛，实际日志保存在dist/p3-f1e1/f1/final-recorded，不会为了追加自身检查日志而改变已封存的原始Linux归档。

## 14. 最终远端验收与 P3 阶段关闭

### 14.1 归档范围与独立签认来源

日期：2026-11-08。本次仅归档已完成的最终验收结论：在文首增加最终状态指引、追加本节，再检查文档diff及受保护文件不变；不重写§1–§13，不修改生产代码、测试、CI、依赖、Requirements、Plan或原始Linux证据，不自动commit或push。

原独立Reviewer在此前源码审查PASS的基础上，仅针对唯一未关闭项E-REMOTE完成了独立复核，明确输出：**E-REMOTE PASS；E-REMOTE可以关闭，P3的NEEDS EVIDENCE可以更新为最终P3 PASS。** 本节记录该实际签认，不把实施者自评或本次文档归档当作新的独立代码审查。

复核优先使用GitHub公开API确认PR、Run、Job、Artifact归属和Git Tree；因gh未登录，实际Artifact ZIP经nightly.link公共代理读取，并重新计算SHA256，与GitHub官方API返回的digest及下列记录完全一致。ZIP在内存中核验，未修改原始证据。本次归档未重新运行测试，也未触发远端CI。

### 14.2 最终受测版本与远端工作流

| 项目 | 已核验记录 |
| --- | --- |
| PR | [#7：Refactor/p3 trade errors](https://github.com/riiy/emtl/pull/7)，MERGED，base为master |
| 最终受测Head SHA | [`576d0bc339c1adc75c2dfac05d65b271c2bb764e`](https://github.com/riiy/emtl/commit/576d0bc339c1adc75c2dfac05d65b271c2bb764e) |
| Merge Commit | [`307d1c95feb571e65434a18de0b9c317fdf390a6`](https://github.com/riiy/emtl/commit/307d1c95feb571e65434a18de0b9c317fdf390a6) |
| Build Run | [42433386429](https://github.com/riiy/emtl/actions/runs/42433386429)，completed / success |
| Build Jobs | check、docs、py311-cover (ubuntu)、finish全部success |
| Offline Run | [42433386452](https://github.com/riiy/emtl/actions/runs/42433386452)，completed / success；offline Job为success |
| 两个Run的事件与版本 | event均为pull_request，head_sha均为上述最终受测Head SHA |
| Artifact | [13598567933：offline-test-evidence](https://github.com/riiy/emtl/actions/runs/42433386452/artifacts/13598567933)，属于上述Offline Run，复核时未过期 |

GitHub官方Artifact digest与实际ZIP重新计算的SHA256均为：

```text
f3e60032ea58e8b282523e7e84aa07237a37c56baead0e6b963cb286784012d3
```

### 14.3 远端Artifact实际核验结果

实际读取的ZIP包含docker-build.log、docker.log、container.log、commands.json、image.json、network-mode.txt、container-exit-code.txt、host-status.txt、三份完整JUnit、coverage.json/xml、tox-result.json、versions.json、synthetic-environment.json及逐命令日志。

| 验收项 | 实际结果 |
| --- | --- |
| Docker平台 | linux/amd64 |
| 系统禁网 | NetworkMode=none；OS网络隔离探针输出OS network namespace isolation verified |
| 容器退出码 | 0 |
| Host状态 | original=0 logs=0 inspect=0 copy=0 cleanup=0 evidence=0 |
| junit.xml | 467 passed；failures=0、errors=0、skipped=0 |
| outside-junit.xml | 467 passed；failures=0、errors=0、skipped=0 |
| explicit-junit.xml | 467 passed；failures=0、errors=0、skipped=0 |
| 节点一致性 | 三份JUnit节点集一致，各467个唯一节点；为同一套测试的三轮运行，不是1401个独立测试 |
| Coverage | 综合94.44%；Statements 95.20%；Branches 91.23% |
| tox凭证隔离 | 真实commands_pre在pytest启动前输出account environment isolated；父环境为合成P1_FAKE_VALUE哨兵 |
| 工具版本 | Python 3.11.18、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2、tox 4.67.13 |
| 命令退出 | commands.json记录的五个原驱动步骤均退出0，保留默认tox、仓库外不同顺序及显式tests/三个入口 |

以上为最终受测Head对应的**远端CI Artifact**结果，与§3–§13的本地macOS/Linux验证分开记录，不把本地结果改称远端CI，也不以覆盖率或累计运行数量单独判定资金安全。

### 14.4 Head、Merge与master的Git Tree

GitHub API独立核验结果：

| 版本 | Tree SHA |
| --- | --- |
| 最终受测Head Commit | `4e87bc9c41e5ce09cccde0b284487b48566def0c` |
| Merge Commit | `4e87bc9c41e5ce09cccde0b284487b48566def0c` |
| 复核时远端master | `4e87bc9c41e5ce09cccde0b284487b48566def0c` |

三者完全一致；受测Head与合并提交SHA不同，但代码树相同。上述Head、Merge与Tree标识的是已经完成远端验收的版本；本次后续文档收尾不属于该受测Tree，不将文档收尾提交描述成新的生产代码验收提交，也不改写原Artifact或其SHA256。

### 14.5 最终Review与阶段结论

- **P3整体最终PASS；E-REMOTE关闭。** 此前源码独立Review PASS与本次E-REMOTE PASS共同完成最终验收闭环。
- **R1/R2/R3缺陷均已关闭。** 原始Review FAIL、各轮修复及红绿/变异记录、历史NEEDS EVIDENCE、446/467测试结果、本地Linux验证和远端证据产生前的状态均按原文保留，不追溯改称当时已经PASS。
- 没有新增交易重试、重登重放或自动补偿；原有旧API、CLI的兼容边界得到保留。TradeOutcomeUnknown仍不是重发许可，非HTTP原异常、内存context/APM及旧API既有风险的限制不因阶段关闭而消失。
- **P3已正式完成并合并至master。后续进入P4，P3不再扩大实施范围。** 本次仅完成验收文档归档，不实施P4；P4按其独立需求、计划与授权开展。
