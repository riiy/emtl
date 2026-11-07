# emtl P1 离线测试体系完善：完整实施计划

## 1. 状态、基线与执行权限

- 状态：待人工批准的实施计划，不是实施或验收报告。
- 分析日期：2026-11-06；阶段仅限 P1；测试目标运行时为 Python 3.11。
- 分析仓库：`/Users/lld/emtl`；工作分支：`refactor/p1-offline-tests`。
- 分析 HEAD：`2d8929b6b3df88131419e89b868a4cdb0b81c7a3`，提交为 `docs: define P1 offline testing requirements`。
- 本地 `master` 与本地远端跟踪引用 `origin/master` 均为 `41f6869fd9e30175bad0264ce732c16c5da715cd`，已合并 P0。未 fetch，不能把本地远端跟踪引用视为已即时核验 GitHub 状态。
- 分析时 `git status --short --branch --untracked-files=all` 仅显示当前分支，无 tracked/staged/untracked 改动。
- 最终归档目标：`docs/refactor/plans/P1-plan.md`。
- Plan 模式保存位置：`/Users/lld/.opencode/plan/P1-plan.md`。本次只保存此计划，不修改项目文件。人工批准后，切换 Build，由 Build 先仅归档计划；实施需有明确实施授权。
- 不自动 commit、push、tag 或发布。远端 CI 运行以人工批准的推送/PR 或人工触发为前提。

### 执行前必读

1. `AGENTS.md`。
2. `docs/refactor/requirements/P1.md`。
3. `docs/refactor/requirements/P0.md`。
4. `docs/refactor/plans/P0-plan.md`，尤其第 16–17 节；后续批准调整覆盖历史设计。
5. `docs/refactor/contracts/P0-public-api.md`。
6. 本计划，以及 `src/emtl/`、全部 `tests/`、根 `conftest.py`、`pytest.ini`、`tox.ini`、`.coveragerc` 和相关 CI 配置。

若源码、需求或基线发生实质变化，先重新核对风险矩阵并修订计划，再执行受影响步骤。

## 2. 目标与兼容性边界

### 交付目标

建立支持 P2 架构重构的最小充分离线回归安全网：认证、查询、下单、撤单、行情的请求契约、返回结果、失败传播、发送次数、日志安全均有有效断言；完整测试集至少在一次 Linux CI 容器禁网条件下通过。

### 必须保留

- `tests/test_api_contract.py` 已锁定的九项包级导出、顺序、函数绑定、签名、参数默认值、注解及子模块接口。
- 查询和下单 JSON 原样透传，不验证或重解释业务 `Status`；撤单仍返回去首尾空白的字符串。
- 登录的独立环境回退、strip、密码加密调用、验证码流程、认证 POST 后提取 HTML 令牌的顺序。
- 原请求 URL、headers、表单字段、参数类型、现有 timeout 有无以及真实交易调用语义。
- 非 200 响应当前的裸 `raise`；普通调用场景下产生 `RuntimeError`。
- `create_order()` 两次 `json()` 求值及第二次结果返回；订单/撤单不自动重试。
- `emt`、`python -m emtl`、CLI 参数/互斥项/退出码；P0 已批准的正常 stdout 为空且不执行交易。
- P0 批准的 checkout 测试入口：仓库根 `python -m pytest`、`python -m pytest tests/`、仓库外显式绝对 `tests/` 路径。不得恢复 `pytest --pyargs emtl`。

### 范围外

生产代码重构、TradingClient、并发隔离、会话生命周期、统一异常、新返回模型、增加交易重试、生产超时策略、OCR 递归策略修复、包最低版本迁移及发布配置清理，分别留待后续获批阶段。

P1 默认不改任何 `src/emtl/` 生产文件。新测试揭示实质资金风险或兼容性缺陷时，单列缺陷与阻断建议，获得批准前不得通过修改生产逻辑让测试通过。

## 3. 已核实的源码事实

以下行号以本计划 HEAD 为准，不代表独立动态验证结果。

| 位置 | 已核实行为 | 测试设计含义 |
| --- | --- | --- |
| `core.py:18–21` | 导入时初始化 OCR、Session、全局认证状态 | guard 与假 OCR 必须先于包导入；每例隔离全局状态 |
| `core.py:41–44` | 先读取 `resp.status_code`，非 200 记录固定日志后裸 raise | `session.post() -> None` 导致 `AttributeError`；400/500 不会走包装函数的假值返回分支 |
| `core.py:47–69` | 无 token 调用 login；URL 直接拼接返回 token；只有 `req_data is None` 才补默认表单 | login 返回 None 导致拼接 `TypeError`、业务 POST 为零；显式 `{}` 不应变默认表单 |
| `core.py:72–86` | OCR 真值才转 int；转换异常递归；假值直接返回 | 空串/None/False/0 均原样流入登录表单；有限非法后恢复已有回归 |
| `core.py:89–99` | 正则要求固定属性顺序；首个匹配值 strip 后写全局 token；无匹配不清除旧 token | 缺 token、空白 token、旧 token 保留必须区分；真实 HTML 变体支持未知 |
| `core.py:102–138` | 回退判断早于 strip；登录 JSON 只解析/格式化、不读 Status；只捕获 try 内 KeyError | 纯空白显式参数不会回退环境；业务拒绝 JSON 仍会尝试 GET token；其他异常传播 |
| `core.py:141–198` | 六个查询包装函数只按 response 真值判断是否解析 JSON | 包装层 None/假值可用局部 seam 测试，但不得冒充真实 HTTP 错误路径 |
| `core.py:201–222` | 表单不做类型转换；真值响应解析 JSON 两次 | 买卖字段、第一次/第二次解析失败及单次 POST 均需断言 |
| `core.py:225–233` | 输入 strip；输出 text.strip；无循环/重试 | 失败文本同样原样返回；网络异常传播，不解释撤单是否成功 |
| `core.py:24–38`、`utils.py:34–37` | 行情状态无效返回 NaN；价格先 strip 再 float | 缺字段 KeyError；空串 0.0；非法字符串 ValueError；None/数字 AttributeError |
| 根 `conftest.py:7–18` | 模块加载即清账户环境、runpy 安装 guard；pytest_unconfigure 恢复 | 覆盖 collection；恢复正确性尚无专门动态测试 |
| `tests/_offline.py:26–62` | 拦截 requests request/send、TCP 建连和数个 DNS API；可安装/恢复 | 不自动继承到新解释器；尚未拦截 getnameinfo、sendto 等路径；幂等恢复未验证 |
| `tests/conftest.py:18–35` | 每例替换 session/get/ocr、清 token/环境；fake_captcha 使用假 HTTP/OCR | 复用此底座；不得 mock 真正被测的验证码函数制造覆盖 |
| `tests/test_core.py:12–16`、日志测试导入处 | 已有真实 requests.Response 工厂；日志测试跨测试模块导入该工厂 | 提取小型 helper 即可，不需要引入新 Mock 框架 |
| `.coveragerc:4–8` | 已启用 branch 与 src/emtl 覆盖范围 | 保留口径；输出明确的行/分支计数，而非新增无意义覆盖率门槛 |
| `tox.ini:23–49` | whitelist、disallow_pass_env、空账户变量、commands_pre 已存在 | 复用并用实际 tox 进程验证；仅静态断言不足 |
| `.github/workflows/github-actions.yml` | Python 3.11 测试与 docs/check；无系统禁网运行 | 新增独立离线任务，不将 linkcheck 计入离线证据 |
| `ci/bootstrap.py:65–70` 与 CI 模板 | bootstrap 会覆盖生成主 workflow；模板与现文件已有差异 | 独立新增 offline workflow，避免在本阶段重构模板；不运行 bootstrap 覆盖用户配置 |

`setup.py` 仍声明 Python >=3.10，发布 workflow 使用 3.10，formatter target 为 py38；P1 仅以 Python 3.11 验证，不借此迁移这些设置。

## 4. 风险测试矩阵：已有保护、缺口和排除项

“已覆盖”表示读到相应断言，不表示本次 Plan 已执行通过。“补充”见第 5 节。

| ID / 风险 | 已有测试、函数 | 缺口与 P1 决定 |
| --- | --- | --- |
| A1 导入前隔离 | `test_test_safety.py::test_bootstrap_was_installed_before_collection`；根 bootstrap | 已覆盖假 OCR/清账户/request 方法；补充真实负向调用及各支持入口 |
| A2 DNS/TCP/HTTP | `test_guards_precede_socket_transport`、`test_socket_and_dns_are_blocked` | 仅部分 API；补 request/send、connect_ex/create_connection、DNS 家族及数据发送旁路 |
| A3 安装/恢复 | `_offline.install/restore` | 幂等、两轮安装恢复、既存/不存在 OCR 模块、未安装 restore 尚缺；必须在隔离子进程验证 |
| A4 子进程入口 | 仓库外 checkout 子进程、`test_cli.py`、日志导入子进程 | 保留；补子进程主动负向调用；不声称普通新进程继承 monkeypatch |
| A5 系统禁网 | P0 文档记录 macOS 沙箱；当前 workflow 无此步骤 | P1 新增 Linux Docker `--network none` 完整套件与独立 OS 证据 |
| A6 凭证隔离 | CI 静态检查、tox commands_pre、checkout 假父凭证 | CI 实际注入合成父进程哨兵并运行 tox；防止根 conftest 清环境掩盖 tox 泄漏 |
| B1 登录输入/表单 | `test_login`、`test_login_fallbacks` | 补双方显式覆盖、均为空、空白不回退、完整 headers/次数/调用顺序 |
| B2 验证码 | `fake_captcha`、`test_captcha_invalid_ocr_recovers_without_leaking` | 非法后恢复已覆盖并保留；补假值结果、请求失败/OCR 抛异常传播及次数 |
| B3 登录失败/令牌 | malformed JSON、fallback 无 token、日志 KeyError | 补业务拒绝后仍取 token、GET 错误、token 空白/缺失及旧状态保留 |
| B4 查询请求 | 六 API 参数化 `test_queries`，均有非零业务 Status 透传 | 补各查询失败传播、真实自动登录链、默认/空表单区分、None/假值分层 |
| B5 下单 | `test_auto_login_and_order`、`test_order_exception_is_not_retried` | 仅买单/泛化 RuntimeError；补卖单、成功/拒绝、具体网络异常、响应丢失及双 JSON 异常 |
| B6 撤单 | `test_cancel_order` | 补 URL/headers/单次 POST、失败文本、HTTP 错误、超时/连接断开 |
| B7 行情 | `test_last_price` 五种值 | 补缺嵌套字段、非法数值、HTTP/传输/JSON 异常，并检查 GET 次数 |
| B8 日志 | `test_logging_safety.py` 正常链、OCR、KeyError、URL/Cookie/body、root 配置 | 补网络异常消息哨兵、Authorization/request body/令牌 URL 等独立哨兵；不得只看 caplog.text |
| C1 复用数据 | `response()` 和 inline JSON/Mock | 提取统一工厂，有限稳定合成案例；避免按用例数机械创建 fixture |
| D1 覆盖率 | tox 已用 pytest-cov；P0 历史 41 项 | 重新记录同环境 P0/P1 基线和行/分支增量；数量不作质量门槛 |
| D2 状态污染 | autouse monkeypatch 隔离；少量独立进程 | 全套第二次独立进程运行并改变关键文件顺序；保护原始 Session/环境/日志状态 |
| K1 API/CLI 兼容 | `test_api_contract.py`、`test_cli.py` 全部保留 | 不删除；无必要新增重复签名测试 |
| X1 多账户/并发 | 全局 Session/token 仍存在 | 不属于 P1，P2 处理 |
| X2 统一异常/重试 | 裸 raise、递归验证码、JSON 两次解析 | P1 特征化；行为改进留待获批 P2/P3 |
| X3 实际券商协议 | 未提供经审查的真实响应材料 | 未知、待证据；不调用券商或编造真实错误码/字段 |

## 5. 新增用例与预期断言

### 5.1 通用规则

- 行为测试默认真实执行公共 API → 内部请求函数 → `_check_resp` 链，只替换 HTTP、OCR、随机数、加密等依赖。
- 使用真实 `requests.Response` 表达普通 HTTP 状态、text、json、truthiness；使用有边界的 Mock/PropertyMock 表达特定异常，不让默认 Mock 真值伪装协议行为。
- 逐例断言：请求 URL、关键完整 kwargs、调用次数、结果/异常、副作用。异常对象由测试创建时，优先检查同一对象传播。
- 对需要单次业务 POST 的用例预置假 token，避免把认证 POST 与委托 POST 混为一谈。另用单独真实自动登录链测试区分认证 URL 和业务 URL。
- 包装函数的不可自然构造分支可以单独替换 `_query_something`，但明确命名为 wrapper seam；此类用例不能充当无重试、HTTP 或端到端行为证据。
- 合成异常包含固定假秘密；测试不得将捕获到的真实环境变量写入日志、断言消息或 artifacts。

### 5.2 登录和验证码（`tests/test_auth.py`）

1. 保留并迁移现有登录用例，参数化以下输入：双方显式、双方环境回退、各自独立回退、参数和环境均空、显式纯空白且环境非空。
   - 断言 strip 后 userId/密码加密输入、duration 原样、完整登录表单及 headers。
   - 纯空白为真值，strip 后为空，不回退；空凭证当前仍进行假验证码及假 POST，不添加参数校验预期。
2. OCR 返回 `""`、`None`、`False`、`0`：不递归、不转整数；一次验证码 GET/OCR；login 的 identifyCode 保留原值及必要类型区别。
3. 保留非法 OCR 后合法的有限两次识别测试，真实执行 `_get_captcha_code()`；禁止替换此函数。只用有限 side_effect，防止测试无限递归。
4. 验证码 HTTP 非 200、Timeout、OCR classification 抛异常：异常按现有代码传播，认证 POST 为零；不引入错误恢复预期。
5. login 非 JSON：传播解析异常，token GET 未调用；现有 KeyError 捕获测试继续保留。
6. 合成业务拒绝 JSON（沿用当前合成 `Status: -1`，不宣称券商真实错误码）：仍执行 token GET；没有匹配返回 None，有匹配则返回 token。锁定代码未判断 Status 的事实。
7. token HTML：正常值 strip、无匹配、匹配纯空白、多个匹配取第一个。无匹配保留之前全局 token；纯空白匹配将 token 设为 `""`。
8. token GET 非 200/Timeout/ConnectionError/读取 text 异常：按现有控制流传播；try 内 KeyError 返回 None；其他异常不吞掉。保持认证 POST、GET 各自的次数。
9. 自动登录失败返回 None 时，真实 `_query_something()` 在 URL 拼接处抛 TypeError，业务 POST 为零。记录已有异常设计，不“修复”为认证异常。

### 5.3 查询（`tests/test_core.py`）

1. 保留六查询 API 的 tag、历史字段、业务非成功 JSON 透传；增加单次 POST 和完整请求 kwargs 断言。
2. 直接验证 `_query_something`：有 token 不登录；无 token 使用一次真实 login 链，先认证 POST/取 token，再业务 POST；默认表单仅用于 None，显式空 dict 保持为空；headers 不污染 `_base_headers`。
3. 参数化六个查询包装函数的代表性失败：Timeout、ConnectionError、HTTP 500、无效 JSON，确认异常不被包装函数吞掉；不扩展无意义字段笛卡尔积。
4. `_query_something` 的 POST 返回 None：AttributeError，单次 POST；不能断言为返回 None。
5. 单独 wrapper seam 覆盖各查询 `_query_something -> None/False` 时返回 None，不调用 json。
6. 原样 JSON 可用嵌套 dict 和一个非 dict JSON（如 list）证明不增加 schema；不为每个 JSON 原子类型新增重复测试。

### 5.4 下单（`tests/test_orders.py`）

1. B/S 两方向，明确合成成功/业务拒绝案例，断言 `stockCode/tradeType/zqmc/market/price/amount` 的值与类型、URL、headers、单次 POST；不对 stockCode 或 market 额外 strip。
2. 保留“两次 JSON、返回第二次结果”独立断言，两个不同结果对象应检查第二次对象身份。
3. POST 抛 `requests.exceptions.Timeout`、`ConnectionError`、`ChunkedEncodingError`：异常原样传播、POST 恰好一次。
4. 响应丢失模型：POST 替身先记录合成已提交事件，再抛连接中断；断言一次事件、一次 POST、异常传播，不将异常解释为“未成交”或“未提交”。测试不能证明服务端是否接受。
5. HTTP 500（必要时补一个 4xx 代表）：普通调用抛裸 raise 的 RuntimeError，POST 一次，json 不调用；不误当作 response 假值导致 None。
6. 响应为 None：AttributeError，POST 一次；响应 body 非 JSON：首次解析抛错，POST 一次。
7. 第一次 JSON 抛错、第一次成功第二次抛错：分别断言解析次数 1/2、异常对象和一次 POST。第二次成功原样返回。
8. 独立 wrapper seam：None/False 返回 None；不与上述真实请求链测试合并。

所有可产生委托的失败用例必须检查 `session.post.assert_called_once()` 或同等严格的实际 Mock 调用记录，不能只断言“调用 API 抛错”。

### 5.5 撤单（`tests/test_orders.py`）

1. 输入/输出 strip、空白输入当前仍发送空 revokes、任意成功/业务失败文本均为 str 原样返回（仅去边界空白），空文本返回空串；不尝试 JSON 解析。
2. 每例检查 cancel URL、headers、表单、恰好一次 POST。
3. HTTP 非 200、Timeout、ConnectionError、响应中断/丢失、None response、text 读取异常：按源码传播，无第二次 POST。
4. wrapper seam 的 None/False 返回 None；说明当前撤单源码无重试，不新增重试或业务状态判断。

### 5.6 行情（`tests/test_core.py`）

保留 NaN/正常/空白价格案例，并补：

- status=0 缺 realtimequote、缺 currentPrice：KeyError。
- currentPrice 非数字文本：ValueError；None/数值对象无 strip：AttributeError；空串：0.0。
- 非 200：RuntimeError；GET 超时/连接错误：原异常；错误 JSON：解析异常。
- 全部检查 GET URL、strip 后 id、market、headers、一次调用；无需真实行情。

### 5.7 日志（`tests/test_logging_safety.py`）

- 保留 DEBUG 级捕获、root logger 配置子进程、CLI、OCR 恢复等现有保护。
- 给用户名、明文密码、加密串、验证码、validatekey URL、Cookie、Authorization、请求正文、响应正文和异常消息分配不同的 `P1_FAKE_*` 哨兵。
- 覆盖登录失败、查询 HTTP 错误、下单/撤单网络异常、响应解析异常；尽量复用上述场景的依赖布置，不复制一整套业务矩阵。
- 检查 emtl 主动生成的 LogRecord：格式化 message、msg、args、exc_info、exc_text、stack_info 不携带哨兵；固定事件记录仍能被宿主捕获。对本来无日志的异常路径允许空记录，但必须验证业务调用/异常确实发生。
- 只保证 SDK 主动日志；调用者打印返回值/异常、外部 HTTP wire trace 不在本阶段保证范围。

## 6. 离线底座补强方案（P1-A）

### 6.1 保留安装层级

继续由根 `conftest.py` 在 collection 前安装网络 guard/假 OCR，`tests/conftest.py` 每例重置依赖及状态。支持入口沿用 P0；不引入 pytest-socket、新插件框架或生产依赖注入参数。

审查实际加载次序：第三方 pytest 插件可能早于根 conftest 加载；Python guard 不是任意启动过程的系统沙箱。CI OS 隔离从整个测试进程启动之前生效，覆盖 collection、测试、teardown 和子进程。

### 6.2 安装/恢复的安全自检

新增 `tests/test_offline_guard.py`，使用新的受控子进程：

1. 导入标准库/requests，先把所有待测网络原始入口替换为只记录调用并抛固定错误的底层哨兵；再按文件路径加载 `_offline.py`。
2. 验证 install 两次仍只保存一份原状态；restore 两次无副作用；再次 install/restore 正确。
3. 分别预置/不预置 `sys.modules['ddddocr']`，检查对象身份与恢复；不导入真实 OCR。
4. 请求负向验证要求出现精确 guard 固定异常、底层哨兵调用数零；restore 后验证恢复的是这些安全哨兵，而非调用真实网络。
5. 不在主 pytest 进程执行 guard restore；不把根 runpy 实例和另一次 import 实例混为同一个状态对象。
6. 根 conftest 的账户环境恢复在专用子进程用合成值/无值两种状态验证；可先以 pytest.main 运行单一 bootstrap 测试，再检查返回后的环境与 guard 恢复。外层保留独立安全哨兵，不在恢复后发送真实请求。

### 6.3 负向接口与边界

- requests：顶层 get/post、Session.request、Session.send；验证码 `core.get` 别名通过实际源码链或受保护新进程验证。
- socket：connect、connect_ex、create_connection、getaddrinfo、gethostbyname、gethostbyname_ex、gethostbyaddr。
- 补 `getnameinfo` 与数据发送入口 `send`、`sendall`、`sendto`，以及平台存在时的 `sendmsg`，防止 UDP/已连接 socket 绕过仅建连保护。
- 新入口仍使用统一固定错误，不带 URL、参数或敏感正文；扩展 `_offline.py` 的同一可恢复列表，不建立第二套 guard。
- 即使 guard 被回归破坏，负向测试仍只能命中底层安全哨兵；不得用真实券商地址或真实 DNS 查询来检验 Python guard。
- CLI/日志子进程继续显式先 bootstrap 再导入 emtl；仓库外 pytest 子进程走批准的 checkout 路径加载根 conftest。增加一次子进程内 HTTP/DNS 主动失败验证。
- 不承诺拦截任意恶意进程、预先保存的原始函数、原生扩展或任意外部工具；这些执行期外网能力由 CI 容器隔离约束。若新阻断影响正常测试基础设施，查明具体原因，不能恢复联网兜底。

## 7. Fixtures 与 Mock 标准化（P1-C）

### 最小文件集合

- `tests/helpers.py`：迁移现有 Response 工厂，明确 value/text/status 的互斥和编码语义；每次新建 Response。提供基于测试目录的简单 fixture 加载函数和共享 `OFFLINE_HELPER` 路径即可。
- `tests/fixtures/protocol_cases.json`：有限、业务命名的合成案例：登录接受/拒绝、资产查询、订单查询/下单结果、交易业务拒绝、撤单原始文本、token HTML。可按可读性拆成少量 JSON/HTML/TXT，而非一场景一文件。
- `tests/fixtures/README.md`：来源为人工合成、依据的源码/现有样本、已知与未知字段、复用方式、禁止真实数据。
- `tests/test_fixtures.py`：只检查会被测试依赖的重要字段/类型，以及必要跨响应关联；不复刻整份 fixture 的镜像断言。

### 协议真实性边界

当前代码与 P0 测试只能确认字段大小写和透传行为；`Status: -1` 是已有合成样本，不是已验证的券商错误码。`Wtrq/Wtbh` 的命名及 `日期_编号` 组合来自 cancel_order 文档；可建立一个明确人工合成的下单→查询→撤单关联样本，不能声称掌握完整成功/失败 schema。

资产字段名、真实拒绝码、完整登录错误结构、实际撤单成功格式、HTML 其他形式均为“未知、待证据”。缺乏依据时采用最小 opaque payload 测试透传，不填造看似真实的金额、持仓或错误码。token、订单 ID、用户名均须明确虚构，且不存在真实账户映射。

无效 JSON、空值、单个非法价格等小样本继续内联。需要逐次 JSON 结果或抛异常时，在 Response 实例上显式替换对应方法；不把 json 解析规则重写进通用 fake。

### 可合并/迁移的现有测试

| 现有内容 | 处理 | 不得丢失的保护 |
| --- | --- | --- |
| test_core 中 login/fallback/malformed JSON | 迁入 `test_auth.py` 并扩展 | 环境回退、表单、token、JSON 失败 |
| test_auto_login_and_order | 将自动认证与订单双 JSON 断言拆成更明确用例 | 无 token 路径、请求表单、两次 JSON、一次 POST |
| test_order_exception_is_not_retried | 纳入具体异常参数化集合，可保留 RuntimeError 一例 | 异常传播与单次 POST，不能只保留成功路径 |
| test_cancel_order | 迁入 `test_orders.py` 并参数化必要文本状态 | 输入/输出 strip 与返回 str |
| test_non_200_preserves_bare_raise | 保留一个直接契约断言，端到端错误用例另验证调用链 | 裸 raise 行为 |
| response 工厂与跨测试导入 | 移至 helpers，日志/行为测试共同使用 | requests.Response 真实 truthiness/解析语义 |
| HELPER 跨 test_cli 导入 | 移至 helpers 或局部 Path 常量 | 子进程导入前 guard |
| 重复日志检查循环 | 可抽取小型检查函数 | msg/args/异常字段不能缩减为只检查文本 |

API 签名测试、CLI 入口测试、非法 OCR 真路径回归、root logger 回归和 P0 安全入口断言不删除。每次删除/合并记录旧 nodeid → 新 nodeid → 保护不变的证据；不以测试数量作为保留或删除依据。

## 8. CI 系统禁网设计（P1-A/D）

### 8.1 选择与边界

新增独立 `.github/workflows/offline-tests.yml`，在 Ubuntu runner 上构建测试镜像，再用 Docker `--network none` 运行完整离线测试集。保留主 workflow 的 tox/check/docs 流程；新 workflow 不经过现有 bootstrap 模板生成，不修改或运行 bootstrap。

- 联网准备：checkout、镜像拉取、依赖安装、tox 环境/项目安装、构建镜像。
- 禁网执行：独立 OS 探针、真实 tox commands_pre、pytest collection、完整 suite、子进程、覆盖率生成与第二次关键顺序验证。
- 联网收尾：宿主上传 artifacts，必要的外部覆盖率服务；不在测试容器内上传。
- docs linkcheck 保留在线任务名称/说明，不计入禁网测试结果。

Docker network none 允许容器内部 loopback，不等于禁止每个本地 IPC。它隔离外部网络；Python guard 仍禁止支持入口中的意外 HTTP/socket 调用。容器不使用 host 网络、特权模式、Docker socket、宿主 home 或凭证挂载。

### 8.2 新文件职责

1. `ci/offline.Dockerfile`
   - 使用 Python 3.11 Linux 基础镜像；记录实际 digest/平台，首次验证后选择明确可复现的标签或 digest。
   - WORKDIR 固定 `/workspace`。
   - 选择性 COPY 源码、测试、根 conftest、打包必须的 README/CHANGELOG/setup/pyproject、pytest/tox/coverage 配置、workflow 静态检查需要的文件、契约下载目标及相关 docs。不得 COPY 开发者 home/凭证目录。
   - 联网构建期间安装 `tox>=4.67`，执行 `python -m tox -e py311-cover --notest -v`，完成测试依赖和项目安装。不能运行交易测试或真实 OCR。
   - `setup.py` 已有 scm fallback_version；无 `.git` 的构建必须验证包元数据和 `emt` 脚本存在。不为容器修改生产版本配置。
   - 执行期设置 `PIP_NO_INDEX=1`、禁用 pip 版本检查；环境仍缺依赖时失败，不在线补装。
2. `.dockerignore`
   - 排除 `.git`、`.venv`、`.tox`、缓存、coverage/build/dist、`.env` 类本地文件、生成 `_version.py` 等；配合选择性 COPY，避免开发者本地构建把无关文件带入镜像。
3. `ci/check_offline_network.py`
   - 只用于独立容器 OS 自检，不导入 emtl、requests 或 `_offline.py`，不使用 Python guard。
   - Linux 检查仅 loopback、无外部默认路由；在宿主已确认 NetworkMode=none 后，直接 TCP 连接文档保留地址 `192.0.2.1:9`，预期内核返回无路由等明确网络隔离错误；不能将任意异常或超时均算成功。
   - 错误类别不符合预期则停止；不探测真实券商/公网服务。记录固定结论，不输出敏感环境。
4. `ci/check_test_environment.py`
   - 将现有 tox commands_pre 中的账户隔离断言迁至易审查脚本，保留空 EM_USERNAME/PASSWORD 语义、其他 EM_* 不穿透、P0/P1 合成账户哨兵及 NETRC/SSH 代理不穿透的检查。
   - 只打印固定成功/失败原因，不输出变量值或整个环境。
   - 在 pytest/bootstrap 清环境之前执行，避免假通过；不导入 emtl。
5. `ci/run_offline_tests.py`
   - 小型标准库驱动：执行 OS 探针、记录工具版本/命令/退出码、调用真实 tox、生成 JSON/XML/JUnit、执行第二次测试顺序、返回真实失败状态。
   - 所有子进程设置合理 timeout；不吞异常，不在失败后返回 0，不接受 skip 作为系统禁网成功。
   - 结果保存在容器 `/workspace/dist/p1-offline/`，宿主仅复制该目录。失败也保留已生成诊断。

### 8.3 容器内测试策略

第一轮：在合成父环境变量下，通过真实 tox 执行 `py311-cover` 全套，保留 commands_pre，输出 `-vv`、term-missing、XML、JSON、JUnit。tox 使用已准备环境和 `--skip-pkg-install`；若 tox 仍要求重新准备依赖导致失败，修改准备/执行边界并重新验证，不能放开 runtime 网络。

合成变量由驱动进程在启动 tox 时构造：`EM_USERNAME/EM_PASSWORD/EM_P1_SENTINEL`、`P0_FAKE_ACCOUNT_CREDENTIAL/P1_FAKE_ACCOUNT_CREDENTIAL`、`NETRC/SSH_AUTH_SOCK/SSH_AGENT_PID`。值固定为显眼的假值。workflow 不引用交易 Secrets，也不需要出现 EM_USERNAME 等变量文本，以继续满足 P0 workflow 静态断言。

第二轮：使用 `.tox/py311-cover/bin/python -m pytest` 在新进程运行整个 `tests/`，将关键文件显式按不同顺序列出，去重后追加剩余文件；保留普通 fixture 隔离、不增加顺序插件。第二轮不累计覆盖率，以免掩盖第一轮分支证据；记录完整命令/nodeids 与结果。

至少在一次运行中验证仓库根默认入口、显式 tests/ 入口和仓库外绝对 tests/ 入口。现有仓库外子进程只覆盖 bootstrap 子集，最终验收还要从外部 cwd 执行完整目录。入口检查与第二轮可组合，避免无目的重复。

### 8.4 宿主验证命令

以下是 Build 阶段命令，当前 Plan 未执行。工作目录为 checkout 根；镜像准备允许联网。

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p1-offline:local .
docker create --name emtl-p1-offline-run --network none emtl-p1-offline:local python ci/run_offline_tests.py
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p1-offline-run
docker start --attach emtl-p1-offline-run
docker inspect --format '{{.State.ExitCode}}' emtl-p1-offline-run
docker cp emtl-p1-offline-run:/workspace/dist/p1-offline ./dist/p1-offline
docker rm emtl-p1-offline-run
```

CI 对 NetworkMode 必须精确断言为 `none`；对容器退出码必须显式断言 0，不能只根据 `docker start` 或 artifact 上传是否成功判断。容器名添加 run ID 避免冲突。使用 always 收集日志/退出码和清理，失败状态仍传播；测试结果缺失也应失败。

CI 触发范围与主 workflow 一致：master push、面向 master 的 PR、workflow_dispatch；最小 `contents: read` 权限，无 Secrets 注入。保存测试报告、coverage XML/JSON、工具版本、OS 探针/NetworkMode、退出码与镜像 ID。上传步骤在容器外执行。

### 8.5 不可用时的替代方案

- 若 runner Docker 权限/镜像依赖不满足：优先在已安装依赖的 Linux runner 使用独立 network namespace（例如经授权的 `unshare --net`）执行同一完整 suite，记录 namespace/路由及内核阻断证据；实施前更新计划和 CI 命令。
- macOS `sandbox-exec` 可作为本地独立断网验证，但不能代替“CI 至少一次系统级禁网完整测试通过”。
- 若两种 Linux 方案均无法执行，允许继续完成已隔离的测试编写，但 P1 系统断网验收为 NEEDS EVIDENCE，阻断最终 PASS/合并；Python Mock 通过不构成替代证据。

## 9. 明确文件修改范围

### 计划内新增/修改

| 文件 | 动作与目的 |
| --- | --- |
| `docs/refactor/plans/P1-plan.md` | 批准后归档本计划，先仅保存计划 |
| `tests/_offline.py` | 按第 6 节补网络入口；保留安装/恢复接口和固定异常 |
| `tests/conftest.py` | 复用/完善依赖及数据 fixture；继续每例状态隔离 |
| `tests/test_test_safety.py` | 补入口/凭证/配置检查；维持 P0 断言 |
| `tests/test_offline_guard.py` | 新增安装恢复、完整负向 guard 自检 |
| `tests/test_auth.py` | 登录/验证码测试迁移与补强 |
| `tests/test_orders.py` | 下单/撤单测试迁移与补强 |
| `tests/test_core.py` | 保留/增强查询、行情，迁出认证/交易用例 |
| `tests/test_logging_safety.py` | 补失败日志哨兵，调整 helper 导入 |
| `tests/test_cli.py` | 仅 helper 路径/子进程公共设施需要的最小调整 |
| `tests/helpers.py` | 小型 Response/fixture 加载帮助函数 |
| `tests/fixtures/protocol_cases.json`、`tests/fixtures/README.md` | 最小合成案例与来源边界；必要少量 HTML/TXT 同目录 |
| `tests/test_fixtures.py` | 关键字段和跨响应关联校验 |
| `tox.ini` | commands_pre 调用隔离脚本，覆盖率输出/报告目录支持；保留主环境和权限白名单 |
| `ci/offline.Dockerfile`、`.dockerignore` | 隔离依赖准备与禁网执行 |
| `ci/check_offline_network.py` | 独立 OS 禁网探针 |
| `ci/check_test_environment.py` | tox 凭证隔离执行检查 |
| `ci/run_offline_tests.py` | 容器验证与可复现报告 |
| `.github/workflows/offline-tests.yml` | 新增系统禁网完整 suite CI |
| `CONTRIBUTING.rst` | 补本地/CI 离线命令、边界与报告说明 |
| `docs/refactor/reports/P1-acceptance.md` | 记录真实结果、矩阵、风险及 Review/CI 链接 |

### 有条件修改

- 根 `conftest.py`：仅安装/恢复自检证明存在问题时，修正测试底座生命周期；不得晚于 collection 安装。
- `.coveragerc`：只有实际报告路径/口径问题时最小调整；保持 branch=true、生产源码覆盖范围。
- `pytest.ini`：仅入口/输出确需调整时修改；默认 testpaths 与禁用旧 pyargs 保护不变。

### 阅读但不计划修改

全部 `src/emtl/`、`tests/test_api_contract.py`、P0 契约/需求/计划、P1 需求、主 workflow、document/release workflow、CI 模板/bootstrap、`setup.py`、`pyproject.toml`、`uv.lock`、`ci/requirements.txt`、pre-commit 配置。

任何超出清单的修改先解释必要性并更新获批范围。构建生成的 `_version.py`、coverage、缓存不是源码交付物；不能把用户已有文件当作垃圾删除。

## 10. 小批次实施、验收、停止与回滚

依赖顺序：S0 → S1 → S2 → S3 → S4 → S5 → S6。遵循先高风险测试、再提取 fixture、最后 CI。每批记录实际命令/版本/退出码，批次边界不是自动提交授权。

### S0：归档、范围与基线

- 文件：批准的计划；验收记录的初始基线。
- 操作：确认分支/HEAD/状态和用户文件归属；记录 Python/tox/pytest/cov 版本；确认预装环境。优先在既有独立 OS 隔离下测 P0 基线，收集行/分支数据。
- 验收：P0 契约/安全测试继续通过；记录历史 41 项与本次真实数量，不能直接复用历史结果。
- 风险：本地缓存不是干净 CI 的依赖证明；运行工具可能生成 ignored 文件。
- 停止：源码偏离计划、测试环境无独立安全边界、出现真实凭证/实盘测试。
- 回滚：无生产改动；只撤销本次新建记录片段，保留用户原文。动态基线无法运行则标记待证据，后续 S5 用相同容器环境补齐。

### S1：核验并补强测试隔离（P1-A）

- 文件：`_offline.py`、安全测试；必要时根/tests conftest。
- 操作：先添加底层哨兵子进程自检，再扩展 guard；验证安装/恢复、collection、父环境、支持入口。
- 验收：网络/DNS 负向测试精确失败且底层零调用；恢复/重装正确；P0 CLI/导入/契约测试通过。
- 风险：主进程错误 restore 会取消整个 suite 防护；两份 helper 实例的状态可能不同。
- 停止：任何负向用例能够落到真实传输、真实 OCR 初始化、子进程不受保护。
- 回滚：定向撤销该批新增 guard/测试变更回到 P0 安全底座；不删除原 guard、不恢复 live 测试。保留新发现缺陷记录，重新通过 P0 安全测试后继续。

### S2：认证、查询、行情特征化（P1-B）

- 文件：`test_auth.py`、`test_core.py`、必要 fixture 布置。
- 操作：按第 5.2/5.3/5.6 节逐组新增，先沿用现有 Response 工厂；迁移旧测试时保留 nodeid 映射。
- 验收：每组的表单/URL/返回/异常/副作用符合源码；真实自动登录链通过；API 契约通过。
- 风险：误把非 200 false response/None 当成 wrapper 返回；认证失败仍取 token 的行为容易被“优化”。
- 停止：必须改生产代码才能满足期望，或新发现资金风险无法作为既有行为接受。
- 回滚：仅撤销新用例或迁移片段，恢复对应原测试；不能删除失败证据、改成 xfail/skip 冒充完成。风险缺陷交人工决定。

### S3：订单、撤单与日志（P1-B）

- 文件：`test_orders.py`、`test_logging_safety.py`。
- 操作：成功/业务拒绝→具体异常→响应丢失→双 JSON→日志哨兵，逐组验证。
- 验收：所有可产生委托的异常用例均严格一次 POST；异常不被转换为成功或未提交结论；日志无合成秘密；P0 CLI/root logger 继续通过。
- 风险：mock 掉 `_query_something` 会造成无重试假覆盖；用 Mock 默认真值扭曲状态。
- 停止：发现重复提交、日志泄漏或兼容性变化；停止相关批次并提交缺陷建议，不自行修生产实现。
- 回滚：定向撤销该批测试重组，恢复旧订单/日志用例；保留缺陷记录，不能弱化断言换绿。

### S4：最小 fixture/helper 提取（P1-C）

- 文件：helpers、fixtures、fixture 校验、相关测试导入、tests conftest。
- 操作：只提取已证明重复且将被 P2 复用的数据/构造逻辑；移除跨 test 模块导入；记录旧→新用例映射。
- 验收：请求、返回、次数等断言不减少；每次加载无共享可变状态；fixture 结构/必要关联通过；完整 suite 结果不退化。
- 风险：工厂变成隐藏业务逻辑，或 fixture 看似真实但无协议证据。
- 停止：发现敏感/可还原数据、无证据字段或合并导致关键断言丢失。
- 回滚：恢复批次前内联数据和工厂，保留已新增高风险用例；不回滚 S1 防护。

### S5：Linux 禁网 CI 与质量反馈（P1-A/D）

- 文件：第 8 节 CI 文件、tox、贡献说明；必要覆盖率配置。
- 操作：准备镜像→无 guard 的 OS 探针→真实 tox 隔离哨兵→完整 suite/覆盖率→独立进程/不同文件顺序→外部 cwd 完整入口→artifacts。
- 验收：NetworkMode=none、内核隔离证据、真实 tox precheck、全部测试、第二轮、所需报告都通过；容器失败会导致 CI job 失败。默认/显式/外部入口均有记录。
- 风险：Linux OCR 依赖 wheel/安装库、tox 重建、CLI 元数据、报告路径、容器 loopback 边界。
- 停止：执行期要求联网、凭证穿透、报告缺失、禁网未实际生效、测试结果被驱动吞掉。
- 回滚：撤销新增 CI/tox 小批次，保留 P0 安全配置及 S1–S4 测试；P1 标为未完成。替代 OS 隔离方案须有实际证据再恢复验收。

### S6：独立 Review、验收与交付（P1-D）

- 文件：`P1-acceptance.md`；只在真实验证需要时修正本计划偏差记录。
- 操作：执行第 11–12 节，检查 tracked/staged/untracked/ignored 文档；提供 P2 可复用资产清单与未知协议边界。
- 验收：需求验收清单全部满足、独立 Review PASS、远端 CI 通过。
- 风险：本地成功误写为远端通过；被全局 ignore 的新文件漏交付；覆盖率数字代替关键行为判断。
- 停止：Review FAIL/NEEDS EVIDENCE、远端 CI 未通过或未执行、任何兼容性差异。
- 回滚：回到具体失败批次定向修正；已提交内容如需回滚先获授权后定向 revert，不 reset --hard/git clean，不删除用户文件，不恢复交易 Secrets 或 live 测试。

## 11. 验证命令与证据要求

### 11.1 准备与本地批次测试

以下均由 Build 在依赖已安装、guard 已审查后执行；本次 Plan 未执行。测试命令应置于可用 OS 隔离内。当前 macOS 可尝试沿用 P0 已记录方案，但必须重新验证本机可用性：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_test_safety.py tests/test_offline_guard.py -vv
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_auth.py tests/test_core.py tests/test_api_contract.py -vv
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_orders.py tests/test_logging_safety.py tests/test_cli.py -vv
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest -vv
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/ -vv
```

仓库外入口在已批准临时目录作为 cwd 执行，使用绝对 Python/checkout 路径；Linux 容器使用 `/workspace` 对应路径。不要为了测试入口向仓库写临时插件或关闭根 conftest。

### 11.2 覆盖率与基线

容器内主测试命令形态：

```bash
python -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p1-offline/tox-result.json -- python -m pytest --cov --cov-report=term-missing --cov-report=xml:dist/p1-offline/coverage.xml --cov-report=json:dist/p1-offline/coverage.json --junitxml=dist/p1-offline/junit.xml -vv
```

驱动先创建输出目录；保持现有 tox posargs 替换命令的语义与 commands_pre。实际命令须用所安装 tox 版本验证，不能假设参数兼容即算通过。

- P0 历史记录：41 项；总体含分支计分 84.42%，core 94.27%；这些不是本次新测结果，也不是纯行覆盖率。
- 在同一 Python/依赖版本与 `.coveragerc` 口径下记录 P1 改动前基线和改动后结果：num/covered statements、num/covered/missing branches、core/auth/order 相关遗漏及新增用例对应关系。
- 若需要 S5 补基线，在独立临时 checkout/容器内重现本计划 HEAD；仅复用执行设施，不带入 P1 新测试。不得在当前用户工作区 reset。
- 记录旧 baseline 原始报告与 P1 原始报告；依赖版本不同无法严格比较时明确标注，不制造精确增幅。
- 不设置为追数字而新增的总覆盖率 fail-under；未覆盖高风险分支按矩阵逐条解释。

### 11.3 状态污染

第二轮新 pytest 进程改变 auth/orders/logging/core 文件顺序并运行全套，或从外部 cwd 以该顺序完整运行。对产生过污染的具体用例再单独验证；无新问题不无条件反复跑全部测试。

重点检查 token、session/get/ocr、环境、caplog、logger/root handler、fixture 深拷贝。不能依赖上一例已登录，也不能让恢复测试影响主进程 guard。

### 11.4 静态检查和交付审查

使用项目固定 Ruff 0.4.1、Black 24.4.0，检查而非自动改写：

```bash
.venv/bin/ruff check src/emtl tests conftest.py ci/check_offline_network.py ci/check_test_environment.py ci/run_offline_tests.py
.venv/bin/black --check src/emtl tests conftest.py ci/check_offline_network.py ci/check_test_environment.py ci/run_offline_tests.py
git diff --check
git diff --cached --check
git status --short --branch --untracked-files=all
git diff
git diff --cached
git ls-files --others --exclude-standard
git check-ignore -v docs/refactor/plans/P1-plan.md docs/refactor/reports/P1-acceptance.md
```

`git check-ignore` 无匹配退出 1 是正常结果；不得把它当成文档不存在。逐个读取 untracked 新文件；如因全局 ignore 漏交付，只向用户说明并显式处理已审查文件，不改全局 Git 配置。

现有主 workflow 的 check/docs 仍需远端通过。pre-commit 会修改文件，若在 Build 运行必须重新审查实际 diff；docs linkcheck 与依赖下载不属于离线交易测试。不得把未运行的 lint/CI 写成通过。

## 12. 最终验收、报告与停止条件

### 必须全部满足

- [ ] P0 API/CLI、日志、安全入口保护继续通过；用例迁移/合并有映射且无保护减少。
- [ ] 第 4–5 节高风险矩阵各项有用例、源码依据和真实执行结果，含 OCR 假值与恢复。
- [ ] 下单/撤单所有可能提交后的失败均断言一次实际 POST，不宣称失败等于未提交。
- [ ] 查询、交易、认证失败的返回/异常与现有生产行为一致，未批准的可观察变化为零。
- [ ] Fixtures 最小充分、人工合成、无敏感信息/可还原映射；协议未知项明确标注。
- [ ] Python guard 的 collection、运行期、恢复、子进程及支持入口验证通过。
- [ ] CI 至少一次 NetworkMode=none 的完整离线 suite 通过，OS 探针独立于 Python guard。
- [ ] 实际 tox 测试进程在 bootstrap 清环境前通过合成父凭证隔离验证；CI 无真实账户 Secrets。
- [ ] 至少两次独立进程/不同关键文件顺序验证通过，无状态污染。
- [ ] 测试明细、行/分支覆盖率、基线比较、工具版本、命令和退出码可复现。
- [ ] tracked/staged/untracked/ignored 交付审查完成，无生产/P2/P3 越界。
- [ ] 独立 Review PASS；远端新离线 CI 及原必需 CI 通过。

`docs/refactor/reports/P1-acceptance.md` 至少包含：分析/实施 SHA、文件清单、风险矩阵 nodeid 映射、合并/删除旧用例映射、命令/版本/退出码、覆盖率原始报告索引、Docker mode/探针证据、凭证隔离证据、第二轮结果、Review/CI 链接、失败/未验证事项与 P2 可复用资产。

Review 输出 PASS / FAIL / NEEDS EVIDENCE，带文件/行号、最小复现和阻断建议。Review 不修改代码。任何关键证据缺失保持未完成，不用测试数量或 Mock 通过代替验收。

清单满足、独立 Review PASS、远端 CI 通过后停止 P1；不为风格重排、更多 fixtures、额外框架或追逐覆盖率延迟收口。进入 P2 需要新的阶段授权。

## 13. 风险、假设、未知与阻断

| 编号 | 类型与事实 | 处置 / 解除条件 |
| --- | --- | --- |
| B1 | 当前仅 Plan 权限，仓库目标路径不允许写入 | 当前保存允许目录；人工批准并切换 Build 后先归档，再依实施授权执行 |
| B2 | Docker/Linux runner 权限、镜像依赖尚未执行验证 | S5 实际构建与禁网全套通过；否则替代 network namespace 或 NEEDS EVIDENCE |
| B3 | 远端 CI 与独立 Review 本次未执行 | 经批准交付远端运行、独立审查后才可宣告 P1 完成 |
| R1 | login 不判断业务 Status，无 token 也不清旧全局 token | 特征化并列为认证风险；线上影响未知，若需修复先获授权，不改变 P1 生产语义 |
| R2 | 请求响应丢失时服务端是否提交不可知 | 用合成提交事件+异常检验不重发；不建立“异常即未提交”断言 |
| R3 | 裸 raise、双 JSON、空 OCR、验证码递归是已知现状 | 锁定而非修复；出现必须更改逻辑的风险时停止相应批次 |
| R4 | Python guard 不覆盖任意恶意/原生/预导入路径 | 支持入口明确；CI 整个进程树外部网络由容器隔离；无全能沙箱声明 |
| R5 | Docker none 保留 loopback，tox 可能尝试重建环境 | 明确外网隔离边界；全部依赖预装，运行期无网且 PIP_NO_INDEX；重建失败不得联网续跑 |
| R6 | tests 中部分 branch 只能用 seam 构造 | 标注 wrapper 合成分支；无重试/HTTP 证据必须真实执行内部请求链 |
| R7 | 当前完整券商 schema、拒绝码、HTML 变体未知 | 只基于源码/P0样本建合成 fixture；禁止抓取真实响应或臆造协议 |
| R8 | 打包安装会生成 ignored 文件；CI 模板与现文件有漂移 | 独立 offline workflow、选择性 COPY、检查 diff；不顺手重构模板/版本体系 |
| R9 | 合成环境断言可能被 pytest 清环境掩盖 | tox commands_pre 在导入 emtl/pytest bootstrap 前执行并保留结果 |
| R10 | 覆盖率高不等于异常/副作用正确 | 按风险矩阵、请求次数、结果与异常验收，覆盖率仅反馈 |

假设：阶段仅批准 P1；可准备 Python 3.11/测试依赖；所有测试材料均人工合成；不存在必须依赖外网的自动测试。任何假设被推翻时，修订计划或记录阻断，不能降低安全与兼容性门槛。

## 14. 本次 Plan 已做与未做

**已完成只读分析：** 阅读 AGENTS、P0/P1 需求、P0 计划和契约、全部现有测试、相关生产源码、pytest/tox/coverage/打包/格式配置、三个 workflow、CI 模板/bootstrap、贡献文档；核对分支、完整 SHA 与 tracked/untracked 状态。计划中的行为判断来自这些代码。

**未执行：** pytest、tox、覆盖率、lint、Docker、OS 探针、依赖安装、真实 OCR、任何券商请求、远端 CI 或独立 Review。P0 测试/覆盖率数字只引用历史文档，未冒充本次结果。

**本次唯一写入：** 允许目录中的本 Markdown 计划。项目代码、配置、测试和仓库计划目标路径均未修改。

## 15. 批准、实施与最终文档归档状态（追加记录）

第 1–14 节原文完整保留，包含起草时的“待人工批准”、未执行说明及未勾选清单；它们是计划起草时的历史状态，不代表当前实施状态。本节不倒填批准日期，也不将计划中的命令冒称为全部逐条执行过。

### 15.1 本次文档收口计划与授权

- 授权来源：维护者本次明确要求完成 P1 最终验收文档闭环，并提供已独立核实的 CI 元数据、Git Tree、coverage、JUnit 和容器证据。本次不重新授权或实施代码/CI 修复，不进入 P2。
- 修改范围：本计划仅追加状态；更新 `docs/refactor/reports/P1-acceptance.md` 的最终远端验证与证据索引；更新 `docs/refactor/reports/evidence/P1-local-linux/README.md` 的核验/交付说明。三个原始归档日志/JSON 保持原字节。
- 顺序：先核对 Git 状态、两提交树与历史证据；保存本收口计划；再更新文档；最后验证覆盖率算术、文件哈希、相对链接、敏感信息、diff 与禁改目录内容不变。
- 停止条件：输出修改清单、证据索引、明确路径的 Git 暂存建议和剩余事项后停止。不自动暂存、commit、push、merge，不下载依赖、触发 CI、调用券商或真实 OCR。

### 15.2 实际批准与实施状态

- 历史批准：先前会话记录及[验收报告第 1 节](../reports/P1-acceptance.md#1-基线范围与结论)记载本计划已获批准，并获针对 Review FAIL 的六项限定修复授权。这里仅追加已有批准事实；未获得可核查的具体批准时间、审批链接或审批人身份，不编造日期或签名。本次维护者的文档收口授权不充当历史批准时间。
- 实施完成：P1 离线测试与 CI 已实施，受测提交为 `8d0a2303d13a2f9d0c9aafae2f1bbe26bd2ade5d`；后续 SCM 构建/打包环境修正属于实际实施记录，不倒改原计划命令。生产代码未纳入本次修复。
- 合并完成：[PR #3](https://github.com/riiy/emtl/pull/3) 合并提交为 `318fb45a5a279d103049c5adc1974e714847df4e`。本次本地 Git 实查两提交 Tree SHA 同为 `55f8640c1cb3711ce7ac8d31865752fb242eda0a`，完整树 diff 为空。
- 远端验证：维护者独立核实 Offline Run `42199620264` 与 Build Run `42199620359` 均为 `pull_request`，`head_sha` 均为上述受测提交，`conclusion=success`；测试、覆盖率及容器证据见[验收报告第 9 节](../reports/P1-acceptance.md#9-pr-3-合并与远端验收证据)。没有将其改称为 merge commit 上重新运行的 CI。
- 归档状态：本次本地检查确认本计划及四个历史证据文件仍未跟踪，merge commit 也未包含它们；应作为独立文档补交纳入版本控制，不能声称原 PR 已交付这些附件。完整待暂存清单见[验收报告第 10 节](../reports/P1-acceptance.md#10-文档归档核验与交付清单)。
- Review 边界：最近一次独立 Review 为 NEEDS EVIDENCE，未发现新增功能/兼容性回归；本次补齐提交对应关系、覆盖率口径及文档交付说明，不倒改该历史结论或代签最终独立 Review PASS。最终签认与文档提交由维护者完成；无需为本文档任务扩展生产、测试或 CI 修改。
