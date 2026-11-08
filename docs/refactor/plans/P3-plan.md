# emtl P3：交易异常语义与不确定结果处理实施计划

## 0. 状态、交付与授权

- 日期：2026-11-07。阶段仅限 P3；**维护者已明确批准完整计划（含 A1–A7），授权按 S0–S6 实施；不是验收报告**。
- 需求：`docs/refactor/requirements/P3.md`。用户输入中重复拼接的长路径不作为文件名。
- 项目归档目标：`docs/refactor/plans/P3-plan.md`。
- 本次 Plan 模式实际保存：`/Users/lld/.opencode/plan/P3-plan.md`；当前模式只能在该目录写计划。维护者切换 Build agent 并授权归档后，才复制完整本文至项目目标。归档与实施分别授权。
- 不修改生产代码、测试、配置或历史文档；不提交、推送、发布、打标签、创建 PR 或执行真实账户请求。
- 本文独立规定设计、批准项、范围、验证命令、验收和回滚；后续执行无需依赖聊天上下文。
- Python 3.11；全部测试使用合成账户、内存 HTTP/OCR 替身和既有系统级禁网。不读取真实账户秘密。

## 1. 实查基线与证据边界

### 1.1 本地 Git

| 项目 | 只读核对结果 |
| --- | --- |
| 仓库 | `/Users/lld/emtl` |
| 当前分支 | `refactor/p3-trade-errors` |
| HEAD | `ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`，`docs: define P3 trade error requirements` |
| HEAD Tree | `69778264170faad0e5d97dea5f08f44e47654f2a` |
| 本地 master / origin/master | 均为 `e75451e3523d19acd7f308c463ece961d96506d7`，PR #6 文档收尾合并 |
| tracked / staged / untracked | `git status --short --untracked-files=all` 无输出；工作区干净 |
| 根 AGENTS.md | 本地存在并已读取；`git ls-files AGENTS.md` 无输出，不假定远端包含它 |
| P2 文档 | 计划与报告均已跟踪；计划 §23、报告 §8 已记录最终关闭 |

本次未 fetch、未查询 GitHub；本地远端跟踪引用不能冒称实时远端最新状态。

P2 受测提交 `6e2078f7dce9f255d60ce89699d405efc09e0e2f` 与 PR #5 合并提交 `d46a83ac97e9a5c17839bbf514a616484dbb9225` 的 Tree 本地实查均为 `eaf1866ae6fff6c754179feec2626b759e6e38c6`。从该合并提交到当前 HEAD 的完整 diff 仅涉及：

1. `docs/refactor/plans/P2-plan.md`。
2. `docs/refactor/reports/P2-acceptance.md`。
3. `docs/refactor/requirements/P3.md`。

因此当前已跟踪生产源码、测试及 CI 与 P2 最终合并版本一致；P2 文档收尾已合并，无需本阶段补做 P2。

### 1.2 测试基线：历史结果与当前验证分开

- P2 最终归档记载：三种入口各 **350 passed**；P1 原 **168** 项保护保留；最终独立 Review PASS。
- 历史远端 Offline Run：`https://github.com/riiy/emtl/actions/runs/42349163949`。
- 历史 Build Run：`https://github.com/riiy/emtl/actions/runs/42349163936`。
- 历史 Artifact：`https://github.com/riiy/emtl/actions/runs/42349163949/artifacts/13563959800`。
- 历史证据包含 NetworkMode=none、容器退出 0、三份完整 JUnit、行覆盖 387/409、分支覆盖 71/80。数据来自已归档报告，本次没有重新下载验证。
- **本次未运行 pytest、tox、coverage、lint、Docker 或 Kill Test。当前 HEAD 的新测完整基线尚缺，S0 必须实际补齐。** 相同源码树支持历史结果适用性判断，不代替本次执行证据。
- 不在 Plan 期间运行会产生测试临时文件、缓存或报告的完整套件；本次唯一写入是允许目录中的计划。

### 1.3 执行前必读

`AGENTS.md`、P3 需求、本文；P0 公共契约、P2 客户端契约；P1/P2 需求、批准计划与验收报告；`src/emtl/{client,core,_protocol,_coordination,__init__}.py`；订单、客户端认证/业务/并发/日志、API 契约测试；根及 tests conftest、`tests/_offline.py`、`tests/client_helpers.py`、pytest/tox、Dockerfile、离线驱动及两个主要 workflow。

若 Build 的 HEAD、文件或需求发生实质变化，先更新基线和计划，不能机械套用行号。

## 2. 目标、不变量与明确范围

交付目标：显式 `TradingClient.create_order/cancel_order` 的普通异常路径能够准确区分：

1. 已知尚未进入本次交易 POST 的前置失败；不能抛交易结果未知。
2. 已进入本次交易 POST 调用边界，后续出现异常，无法确认券商结果；抛机器可识别的 `TradeOutcomeUnknown`。

保留以下不变量：

- 每次调用最多一次交易 POST 尝试；认证 POST 另计，查询虽也使用 POST 但不是交易提交。
- 没有自动重试、重新认证后重发、补单、补偿撤单、自动查询确认、轮询或恢复交易。
- 不推断券商 `Status` 的业务含义；订单仍两次 JSON 求值且返回第二个对象；撤单仍返回 `text.strip()`。
- 同账户现有 RLock 覆盖前置处理、POST、响应处理及错误转换；异常后释放。不同账户继续允许并行。
- 不改变旧九项模块级 API、`core.get_last_price`、CLI、协议字段、endpoint、既有 timeout、旧裸 raise 或旧认证状态策略。
- 不增加异常基类体系、Result 模型、持久化状态、重试配置、自动断路器或 UNKNOWN 认证状态。

**不能把“没有捕获到 TradeOutcomeUnknown”泛化为“订单肯定没有提交”。** 普通返回本身不确认成交；进程退出、KeyboardInterrupt 等也不在本异常转换契约内。机器分类与单次调用阶段结合使用，不作为重发许可。

## 3. 实际调用图及风险定位

```text
TradingClient.create_order
  -> 账户 RLock
  -> _protocol.order_form（目前只构造 dict，无订单业务校验）
  -> _query_something("create_order")
       -> _ensure_open
       -> NEW 时 login
            -> 清 token/Cookie；AUTHENTICATING
            -> captcha GET -> OCR -> login_form/加密
            -> 认证 session.post(login URL)
            -> _check_resp -> JSON 本地接受门槛
            -> token GET -> 提取 token -> READY
            -> 失败 finally：清 token/Cookie，FAILED
       -> READY/token 检查
       -> _protocol.query
            -> tag/URL/default form/headers/redirect options
            -> 交易 session.post（allow_redirects=False）
            -> _check_resp
       -> _protocol.order_result
            -> response 真值 -> JSON 第一次 -> 固定事件日志 -> JSON 第二次

TradingClient.cancel_order
  -> RLock -> _ensure_open -> cancel_form(order_str.strip())
  -> 同一 _query_something/query 链 -> cancel_result -> 真值/text.strip

六查询 -> 同一 _query_something/query -> json_result（只读业务 POST）
行情 -> RLock -> _ensure_open -> snapshot GET/check/JSON -> last_price

旧 core -> 相同无状态 _protocol helpers
         -> core._check_resp -> _protocol.check_response（旧裸 raise）
```

| 代码位置（当前 HEAD） | 设计依据 |
| --- | --- |
| `client.py:109–145` | login 先清状态，认证 POST 位于 124 行；失败清理保留主异常，不能被交易总 catch 误分类 |
| `client.py:147–154` | 自动登录早于业务 query；只有此后进入交易 tag 的实际 query 才能标记交易尝试 |
| `_protocol.py:16–26` | 请求构造在 POST 之前；POST 后检查响应；适合增加一个默认关闭的发送边界通知回调 |
| `_protocol.py:10–13` | 非 200 固定日志后裸 raise；无活跃异常时 RuntimeError，有活跃异常时重抛它 |
| `_protocol.py:89–98` | 响应真值、两次 JSON、日志和 text.strip 都可能在已尝试 POST 后失败 |
| `client.py:180–195` | 外层方法已持锁直至全部响应处理完成，继续沿用 |
| `tests/test_client_operations.py:186–209` | wrapper None seam 与 status=200 的 FalseResponse 分别有既有契约；不可把它们等同于真实 POST 返回 None |
| `tests/client_helpers.py:93–112` | 已有真实 Session.request/send + 内存 adapter 接缝，可检验隐式 redirect |

源码搜索未发现交易 retry、HTTPAdapter 配置或 auth-resend hook；仅有验证码非法 OCR 后递归。该递归发生在认证前置阶段，保留，但不能由此声称“所有 HTTP 都只发一次”。默认 requests/urllib3 的实际版本及 adapter 行为仍需 S0/S4 离线验证。

## 4. 最小设计比较与推荐

| 候选 | 评价 | 决定 |
| --- | --- | --- |
| 只新增 TradeOutcomeUnknown，非交易 HTTP 用固定 RuntimeError | 类型更少，但没有明确安全状态码接口；状态码要靠字符串或动态属性，诊断契约不清 | 不选 |
| **两个并列异常 + 每次调用局部发送标记 + 一个协议回调** | 精确分开认证/交易，保留旧检查器，能覆盖解码；无新状态机或全局层级 | **推荐** |
| 所有新客户端异常统一包装，另加认证/查询/传输异常类型 | 扩大行为变化，影响原异常身份和认证/OCR/生命周期测试 | 不选 |
| 修改共用 check_response 或使用 raise_for_status | 会改变旧裸 raise；requests HTTPError 可能带 URL/request/response；raise_for_status 还不拒绝所有 3xx | 不选 |
| 在 create/cancel 外无条件 catch Exception | 认证 Timeout、关闭、输入失败都会被误标为交易未知 | 不满足 K1 |
| self._trade_started 或全局共享标志 | 上次尝试污染后续调用、跨实例/重入风险，非必要状态 | 不选 |
| 拆出新的交易传输层或复制 query | 改动大、协议逻辑易漂移；当前一个私有可选回调足够 | 不选 |

推荐最多新增两个生产私有控制点：`_execute_trade`（局部标记和转换）及 `query` 的边界回调；新 `_check_resp` 留在现有方法。没有异常工厂、装饰器框架、策略类或多阶段上下文对象。

## 5. 最小公开异常契约（批准后生效）

### 5.1 导入、继承与字段

新增 `src/emtl/errors.py`，稳定导入路径：

```python
from emtl.errors import TradeOutcomeUnknown, BrokerHTTPError
```

为减少包级兼容改动，**不修改 `emtl.__all__`，不增加包级异常导出**。原九函数与 TradingClient 的严格导出顺序保持。若维护者要求 `from emtl import TradeOutcomeUnknown`，须先批准两项精确追加及对应契约测试调整，不由 Build 自行增加。

两类均直接继承 `RuntimeError`，彼此不继承；不用 requests.HTTPError，不新增共同 SDK 基类。HTTP 特定 handler 不应把交易未知当成一般 HTTP 错误继续处理。

| 类型 | 构造契约 | 稳定可读字段 |
| --- | --- | --- |
| `TradeOutcomeUnknown` | `TradeOutcomeUnknown(operation: str, reason: str, status_code: Optional[int] = None)` | `operation`、`reason`、`status_code` |
| `BrokerHTTPError` | `BrokerHTTPError(status_code: int)` | `status_code` |

`TradeOutcomeUnknown.operation` 仅 `create_order` / `cancel_order`。`reason` 使用三个固定字符串，不新增公开 Enum：

- `exchange_error`：已过发送边界，但 query 尚未正常返回；包括传输异常、响应缺失/不合法、HTTP 状态读取错误。
- `http_status`：收到可读取的整数 HTTP 状态且不为 200；包括 3xx、4xx、5xx，乃至其它非 200 整数；不解释受理情况。
- `response_error`：query 正常返回后，在 response 真值、JSON1/JSON2、固定订单日志、撤单 text/strip 等结果处理阶段抛普通异常。

不额外区分 timeout/connect/decode 子类型，也不携带原异常类名。阶段类别已满足机器识别；不会根据第三方异常字符串做分类。

`status_code` 只在 `reason=http_status` 时填安全的非 200 整数，其余为 None；即使解码前已见 200，也不再次访问响应获取状态。`BrokerHTTPError` 必须有精确 `int` 的非 200 状态码，不接受 bool、float、字符串或自定义对象；operation/reason 必须是精确内建 str 且属于上述白名单，避免不可信子类的格式化行为。非法构造参数用固定 TypeError/ValueError，不回显输入。无需冻结对象、序列化协议、额外 traceback 属性或请求 ID。

### 5.2 消息、日志和原异常

- 消息只由固定模板、白名单 operation/reason、安全整数状态构成。例如 `trade outcome unknown: operation=create_order, reason=exchange_error; do not automatically resubmit`；HTTP 消息如 `broker HTTP status 503`。
- 精确英文句子不作为调用方分支判断依据；字段和值才是稳定契约。
- `args` 只包含安全消息；默认 `str/repr` 安全。不接受或保存 URL、request、response、账户、token、Cookie、参数、正文、原异常字符串或 notes。
- 转换全部使用 `raise NewError(...) from None`，不使用 `from original`，不调用 `str/repr(original)`，不把它放入 logger.exception、exc_info 或任何自建字段。
- 新异常转换不新增主动错误日志；新 HTTP 检查保留 `request failed, code=%s` 固定日志，只在状态通过精确整数检查后记录。既有订单固定日志及其双解析位置保持，不打印新旧异常对象。
- `from None` 令 `__cause__ is None`、`__suppress_context__ is True`，抑制标准 traceback 的隐式上下文输出；**并不物理删除 `__context__`、traceback frame 或 frame locals**。不承诺内存擦除，不实施 traceback/frame 清理框架。
- 安全保证适用于 SDK 构造的这两类异常及正常标准 traceback（不显示 locals）。不承诺第三方 APM、调试器、自定义格式器、主动遍历 context、显式打印原异常、宿主源码行中的秘密字面量也能被 SDK 清洗。
- 丢失原始传输/解码错误详情是明确调试代价；仅靠安全阶段和状态诊断，必要时人工在受控环境定位，不增加调试开关输出秘密。

### 5.3 非交易异常与安全范围

新客户端 `_check_resp` 不再调用旧 `_protocol.check_response`：读取一次 `resp.status_code`，验证精确整数；非 200 抛 `BrokerHTTPError`，200 继续。

- 验证码 GET、认证 POST、token GET、六查询 POST、行情 GET 的有效非 200 状态均为 BrokerHTTPError，绝不是 TradeOutcomeUnknown。
- 状态字段存在但不是精确整数：固定 `TypeError("invalid HTTP status") from None`，禁止通过格式化原字段泄漏；这项新客户端异常变化列为批准项。
- 无 response / 无 status_code / status 属性本身抛错：非交易路径保留原异常；交易尝试后由外层安全转换为 exchange_error。
- 非交易传输、OCR、加密、JSON/text、价格转换、清理/close 等异常保留 P2 原类型和对象传播。login 仍在 finally 清认证态，主异常不被清理异常替换。

**本计划不承诺新客户端所有异常的 traceback 都脱敏。** 特别是 K1 的认证 Timeout、查询带 token URL 的原始 requests 异常仍可能包含秘密；这些是明确保留的 P2 行为。维护者必须批准这一最小范围。若要求这些路径也全部安全包装，应停止并修订兼容差异与设计，不能偷偷复用 TradeOutcomeUnknown 或新增大框架。

## 6. 发送边界与实现方式

### 6.1 边界定义

“尝试交易 POST”定义为：本次 create/cancel 的前置认证和请求构造已完成，即将调用已取得的 `session.post` callable。**不是 TCP 已连接、不是字节已发出、不是券商已受理或已成交。**

请求库内部的序列化、URL 校验或连接错误如果发生在该 callable 内，统一按已尝试处理；即使实际没上网，也不从异常类型推断“可重发”。本阶段不进一步拆 requests 的内部发送状态。

### 6.2 最小代码布置

1. `_protocol.query` 末尾新增私有可选 keyword-only 参数 `on_post_start=None`，保留现有 `disable_order_redirects`。
2. 原 tag 断言、URL 拼接、默认表单、headers、redirect options 全部先完成；取得 `post = session.post`。之后如有回调则调用，紧接着唯一一次 `post(url, headers=..., data=..., **options)`。两者之间不得再加参数处理、登录、日志、检查或其它可失败工作。
3. 回调只做局部布尔赋值，没有 I/O、格式化或异常逻辑。默认 None 路径不改变旧请求 kwargs、检查器、解析或裸 raise 的异常上下文。
4. `TradingClient._query_something` 增加同名私有 keyword-only 参数；维持 open/NEW login/READY 检查在前，只对 create/cancel tag 转发回调。认证函数、查询和行情均不使用它。
5. 新私有 `_execute_trade(operation, data)` 为每次调用创建局部 `attempted=False` 与 `reason="exchange_error"`，定义只设置 attempted 的闭包，调用真实 `_query_something`；正常返回后把 reason 改成 `response_error`，再调用原 `_protocol.order_result` 或 `_protocol.cancel_result`。
6. 该 helper 只服务两项交易，无通用 callable 调度框架。create/cancel 继续持已有外层账户锁并在调用 helper 前构造原表单。保持 create 先 order_form、cancel 先 ensure_open 再 cancel_form 的现有次序。
7. `except BrokerHTTPError as error`：attempted=False 则裸 raise；否则仅提取安全 status_code 转为 TradeOutcomeUnknown(operation, http_status, status_code) from None。
8. `except Exception`：attempted=False 则裸 raise；否则以当前 reason 构造 TradeOutcomeUnknown from None。不捕获 BaseException，不做返回兜底，不吞失败。
9. 保留 `_protocol.check_response`、core 和所有共享结果解析 helper 的原实现。HTTP 新策略只存在于客户端 `_check_resp`，不复制交易协议构造/解析。

这里的异常范围可以包含认证，**但转换的必要条件是局部 attempted=True**；它不是包住整个方法就无条件转换。不得把标记设置在 create/cancel 入口、login 之前或任意 POST 共用层，也不得根据“session.post.call_count>0”判断。

### 6.3 每次调用的状态/信号表

| 阶段 | attempted | 对外信号 | 交易 POST 次数 |
| --- | --- | --- | --- |
| 构造参数、关闭、cancel 输入 strip、请求构造失败 | False | 原异常；HTTP 特殊规则除外 | 0 |
| NEW 自动认证 GET/OCR/认证 POST/token GET 失败 | False | 原非交易异常或 BrokerHTTPError；认证状态清理 | 0 |
| 认证证据不足，FAILED/无 token | False | 固定 RuntimeError(authentication required) | 0 |
| 即将调用交易 session.post | True | 仅内存标记，不公开返回 | 最多 1 |
| session.post 或 check 响应过程抛错 | True | exchange_error，或已知非 200 的 http_status | 1 次尝试 |
| query 返回后结果处理抛错 | True | response_error | 1 |
| 成功走完原返回路径 | True | 原 JSON/文本/既有 None | 1 |

标记不放在 self、Session、认证状态或全局，不在不同调用间复用；一次交易未知后，后续前置失败不能继承“已发单”。添加“第一次未知，第二次前置失败”回归以证伪粘滞标记。

### 6.4 响应合法性与 None 的细分

- 实际 `session.post -> None`、普通无 status 属性对象、非整数 status、状态读取失败：进入 query 后失败，交易归 exchange_error。
- status=200 但真值判断失败：query 已返回，归 response_error。
- status=200、真值为 True 但缺 json/text/strip 或访问失败：归 response_error。
- **status=200 且无异常的 FalseResponse 继续返回 None、不解析 JSON/text**，由既有实际调用链测试锁定。它不是响应缺失，不新增严格 Response 类型/schema 检查。
- 原 wrapper seam `_query_something -> None` 仍可返回 None；它不证明真实底层 None 响应的处理。
- JSON 两次解析成功时，第二次即使是 None/list/Status=-1，也原样返回；不增加业务成功定义。

### 6.5 未知之后的状态、锁与控制权

- 不主动改 token、READY 状态或清 Cookie；HTTP 库对自身 jar 的正常响应处理不在“状态不变”断言的额外保证内。
- 不自动登录或恢复，不新增交易阻断状态。调用方可暂停自己的自动化并人工核对。
- READY 下允许调用方**另一次显式发起**只读查询；不由异常处理自动调用。查询虽用 POST，仍不包装为 TradeOutcomeUnknown。
- 不宣称显式查询能自动确认某次委托。后续人工交易决策属于调用方；SDK 不提供重发建议或幂等保证。
- 锁继续覆盖结果处理和错误转换；with 退出后必须释放。同账户另一实例应能执行自己的合成只读任务。
- KeyboardInterrupt/SystemExit/GeneratorExit 等 BaseException 原样传播；任何此类中断都不是“肯定未提交”的证据。若需要把它们也变成业务异常，须单独批准改变进程控制语义。

## 7. 兼容性差异表（必须逐项批准）

表中“旧行为”指当前 P2 TradingClient；**所有旧模块级 API 均保持当前 P0/P1/P2 行为**。

| 场景 | P2 当前新客户端 | P3 拟议新客户端 | 交易边界/兼容决定 |
| --- | --- | --- | --- |
| 构造缺/错凭证 | 固定 TypeError/ValueError | 不变 | 无交易 |
| CLOSED 操作 | 固定 RuntimeError；保持原参数处理先后 | 不变 | 0 POST |
| cancel 参数无 strip | AttributeError/原异常 | 不变 | 0 POST；不新增订单校验 |
| NEW 认证 Timeout/ConnectionError | 原 requests 异常，清状态 | 不变、非 Unknown | 认证 POST 可为 1，交易为 0 |
| 认证 OCR/加密/JSON/text 出错 | 原异常，失败清状态 | 不变 | 交易 0 |
| 验证码/认证/token HTTP 非 200 | 通常裸 raise RuntimeError；活跃 except 时可重抛该异常 | BrokerHTTPError(status_code) | 新类兼容变化，交易 0 |
| login 证据不足/无新 token | None、FAILED | 不变 | 自动业务调用随后 authentication required |
| FAILED、READY 但缺 token | 固定 authentication required，无自动登录 | 不变 | 交易 0 |
| query 请求构造失败 | 原 AssertionError/TypeError 等 | 不变 | 标记尚未设置，交易 0 |
| 交易 POST Timeout/ConnectionError/ChunkedEncodingError/其它 Exception | 原异常类型/对象 | TradeOutcomeUnknown(exchange_error, None) | 进入一次 POST，改变类型/对象/异常链 |
| 交易 HTTP 3xx/4xx/5xx/其它非 200 整数 | 通常 RuntimeError；可能重抛活跃异常 | TradeOutcomeUnknown(http_status, code) | 不跟随 redirect，不推断未受理 |
| 交易 POST 返回 None/缺状态/状态读取失败 | AttributeError/原异常 | TradeOutcomeUnknown(exchange_error, None) | 请求已尝试 |
| 交易返回非整数 status（含 bool/float） | 比较及裸 raise，某些等于 200 的值被接受 | TradeOutcomeUnknown(exchange_error, None) | 新类有效性变化，批准后实施 |
| HTTP 200，真值判断抛错 | 原异常 | TradeOutcomeUnknown(response_error, None) | 不额外执行真值判断 |
| 下单 JSON 第一次/第二次失败 | ValueError、JSONDecodeError 或原异常 | TradeOutcomeUnknown(response_error, None) | 解析次数仍为 1/2，POST=1 |
| 撤单 text 读取或 strip 失败 | 原异常 | TradeOutcomeUnknown(response_error, None) | POST=1 |
| 订单固定日志 handler 抛普通异常 | 原异常 | TradeOutcomeUnknown(response_error, None) | 已尝试；不自动恢复/补发 |
| HTTP 200 的假值 Response / wrapper None seam | None | 不变 | 不等同成交或响应缺失；保留测试 |
| 正常订单 JSON、Status=-1、非 dict JSON | 第二次对象原样返回 | 不变 | 不解释券商状态 |
| 正常撤单文本（含“rejected”或空串） | strip 后文本 | 不变 | 不解释文本 |
| 六查询/行情有效非 200 HTTP | 裸 raise | BrokerHTTPError(code) | 非 Unknown；新类变化 |
| 非交易有 status 但非精确 int | 比较/裸 raise/可能通过 | 固定 TypeError | 不格式化不可信状态字段 |
| 非交易 None/缺 status/状态 getter 抛错 | 原异常 | 不变 | 不保证第三方原异常脱敏 |
| 查询/行情传输、JSON、价格字段失败 | 原异常；行情某些状态返回 NaN | 不变 | 非 Unknown |
| close/清 Cookie 出错 | P2 原异常及最终生命周期状态 | 不变 | 不扩展异常框架 |
| 活跃 except 中新 HTTP 错误 | 可能重抛外层异常 | 独立安全新异常，from None | 明确消除新类上下文泄漏；旧 core 不变 |
| BaseException 中断 | 原样传播 | 不变 | 不得据此重发 |

旧 API 验收特别包括：`core._check_resp` 普通非 200 的 RuntimeError，以及 `test_legacy_bare_raise_still_reraises_an_active_exception` 的**同一异常对象**重抛。旧订单 kwargs 不添加 allow_redirects；旧认证不清旧 token 的特点不动。旧接口没有获得 P3 安全异常或不跟随重定向的新保证。

## 8. 最小 Kill Test：先失败，再实现

集中新增 `tests/test_trade_errors.py`，复用 `client_factory`、`response`、`ready`、`token_reply`。公开路径必须实际执行 TradingClient → `_query_something` → `_protocol.query` → Session；**正常 Kill Test 只能替换底层 Session/OCR/响应对象，不 Mock 被测公共方法、login、query 或发送标记**。

先加入契约测试和两类异常最小定义，使测试能正常收集；不以 ImportError 当作 Kill Test 红灯。尚未接入转换时，K2/K3 必须因原异常未转换而失败；K1/K4 可在 P2 已通过。

### K1：认证 POST 失败不是交易未知

- NEW 客户端，验证码 GET/OCR 正常；底层认证 POST 先记录 URL/方法，再抛合成 Timeout。
- 分别经 create/cancel 调用；异常仍为原 Timeout，且明确 `not isinstance(..., TradeOutcomeUnknown)`。
- 请求记录严格为允许的验证码 GET 与认证 POST；create/cancel endpoint POST=0、token GET=0，无任何额外请求。
- 认证中写入合成 Cookie 后失败，断言 token 空、FAILED、Cookie 清理。再次业务调用不自动登录。
- 同组增加“认证成功、随后交易 POST Timeout”：允许认证 POST=1、交易 POST=1，后者必须 Unknown。不能用总 POST 数判断类型。

### K2：已就绪交易只尝试一次，失败为 Unknown

- READY 客户端；create/cancel 参数化；交易 post 替身记录“进入本次尝试”，然后 Timeout。
- 精确断言类型为 TradeOutcomeUnknown、operation 正确、reason=exchange_error、status_code=None，且不是原异常对象。
- 交易 URL POST 恰好一次，allow_redirects=False；该操作期间 GET=0、其它 POST=0，整个 HTTP 事件列表只包含该交易。
- 替身只记录调用，不把“模拟已受理”当作真实券商证据。
- token/READY 未被 SDK 失效化，无隐藏 login、补偿查询、cancel 或第二次 create。

### K3：POST 返回后解码失败仍是 Unknown

- 下单第 2 次 json 抛错；第一结果与失败可区分，json.call_count=2。
- 撤单 text 属性抛错，属性调用恰好 1 次。
- 两者 Unknown(response_error)、交易 POST 恰好一次、其它 HTTP 为零。
- 扩展矩阵另测 JSON 第 1 次、text.strip 失败和 response.__bool__ 抛错。

### K4：正常合成业务响应不解释、不重发

- HTTP 200，下单两次 JSON 返回不同对象，第二个为含 Status=-1 的合成字典；断言返回第二个对象身份、完整字段不变、json 两次、交易 POST 一次。
- 另一个非 dict JSON 返回继续原样；撤单“rejected”和空串按 strip 原样返回。
- 不抛 Unknown/BrokerHTTPError，不生成成交/拒绝已确认标记，不产生额外请求。

**K1–K4 任一不满足，先修边界/返回设计，停止扩展其它 API。**

## 9. 补充测试矩阵、现有测试迁移与变异

### 9.1 风险驱动增量

| 风险 | 最小验证 |
| --- | --- |
| 前置失败误分类 | CLOSED、FAILED、cancel(None)、请求构造失败；交易 POST=0；标记仅在实际边界设置 |
| 标记跨调用污染 | 第一次交易 Timeout 后，第二次 cancel 输入错误或关闭后调用；第二次非 Unknown、无新 POST |
| 传输/响应丢失 | create/cancel × Timeout、ConnectionError、ChunkedEncodingError；保留已有事件与次数断言 |
| HTTP/redirect | create/cancel × 400、503、307、308；另一个非 200 整数代表；Unknown.http_status/code；不读 json/text |
| 不合法响应 | None、无 status 对象、status getter 抛错、含合成秘密的字符串 status、bool/float status；Unknown.exchange_error，不格式化对象 |
| 响应处理 | JSON1/JSON2、text getter/strip、真值抛错；Unknown.response_error；原解析次数不变 |
| FalseResponse/JSON None | 继续现有 FalseResponse None 返回、第二次 JSON None 返回；不能以结果 None 一概判 Unknown |
| 非交易 HTTP | 验证码、认证 POST、token GET、六查询、行情；BrokerHTTPError 非 Unknown，状态整数，认证失败清状态 |
| 保留的非交易错误 | 认证 Timeout、查询 Timeout、行情 decode/price 及 cleanup 原异常身份仍成立 |
| 未知后显式查询 | 先断言交易异常期间无其它 HTTP，再由测试显式 query_orders；只产生这次查询，无重新登录，返回原数据 |
| 锁范围/释放 | 同账户两实例，第一项在 JSON2/text 内 Event 阻塞；第二项出现真实锁竞争且未进入 HTTP；释放后第一项 Unknown，第二项完成；不靠 sleep |
| 默认/内存传输 | 现有 Session.request/send 内存 adapter 路径，307/308 adapter.send=1；一次 Timeout handler 也只有一次 adapter.send；默认新 Session adapter 的重试预算为零、无 auth/response 重发 hook |
| 旧兼容 | 原 orders/core/auth/wrapper/logging/API/CLI 全保留；普通及活跃上下文裸 raise 均不变 |

默认 adapter 检查仅构造 Session、读取配置、close，不发网络；记录实际 requests/urllib3 版本。内存 BaseAdapter 证明 Session 层 redirect/hook 调用，**不冒称覆盖 HTTPAdapter 内部 urllib3 重试**；后者需结合默认配置和该版本调用链审查。若发现默认依赖具有可重复交易 POST 的行为，立即阻断，先修订方案，不能擅自增设全局 retry 配置。

### 9.2 标准 traceback 与日志测试

在 `tests/test_client_logging.py` 扩展，不复制整套业务矩阵：

1. 合成 username/password/code/token/Cookie/Authorization/request body/response body 各用不同哨兵；原异常消息、`__notes__`、嵌套 cause 中也放合成秘密。
2. 至少覆盖交易传输、第二次 JSON、撤单 text、HTTP 503 与认证阶段 HTTP 503。
3. 捕获新异常后检查 `str`、`repr`、`args`、稳定字段，以及 `''.join(traceback.format_exception(error))` 不含哨兵；检查 cause=None、suppress_context=True。
4. 额外在外层 `except` 内主动抛带秘密的异常，再执行新客户端 HTTP 错误，证明外层活跃 context 也不进入标准 traceback。
5. 用标准库默认 traceback，不依赖 pytest 的短 traceback 或全局日志过滤器掩盖泄漏。异常源中使用变量取秘密，避免测试源码行直接内联秘密导致无关失败。
6. 延用 `assert_no_sensitive_logs` 检查 LogRecord 的 msg/args/getMessage/exc_info/exc_text/stack_info；不只查 caplog.text。
7. 无 `request/response/original_error` 自建属性；不断言 __context__ 必为空，不在测试报告打印其内容。
8. 非交易原始 Timeout 的身份保留测试继续存在，明确不将此路径伪称为新异常脱敏覆盖。

### 9.3 现有测试的精确调整清单

| 文件/测试 | 仅允许的预期调整 | 必须保留 |
| --- | --- | --- |
| `test_client_operations::test_uncertain_submission_never_replays_or_compensates` | 原 requests 类型/对象 → Unknown(exchange_error) | 全部参数分支、事件一次、POST一次、无GET、token/READY |
| `test_order_bad_response_never_retries` | AttributeError/RuntimeError → Unknown(exchange_error/http_status) | POST一次、无GET；扩展状态码字段 |
| `test_order_each_json_failure_propagates_without_retry` | ValueError/原对象 → Unknown(response_error) | index=1/2、解析次数与单次POST |
| `test_cancel_text_failure_propagates_once` | ChunkedEncodingError/原对象 → Unknown(response_error) | text一次、POST一次 |
| `test_redirect_cannot_resend_order_at_adapter_level` | 裸 raise → Unknown(http_status, 307/308) | 实际adapter一次、POST方法、精确交易URL |
| `test_query_invalid_response_preserves_exception` | 仅 http 分支 RuntimeError → BrokerHTTPError | 六查询、None AttributeError、JSON ValueError、次数 |
| `test_market_price_transport_and_decode_errors_are_not_nan` | 仅 http 分支 → BrokerHTTPError | 其它原类型/对象、GET一次 |
| `test_client_auth::test_authentication_failure_invalidates_state_and_preserves_exception` | 仅 captcha/login/token_http → BrokerHTTPError | 其它原异常身份、token/Cookie失效及各阶段请求数 |
| `test_client_logging::test_client_does_not_log_secrets_in_success_or_failure` | 交易失败精确 Unknown；query HTTP 精确 BrokerHTTPError | 全LogRecord检查；认证非HTTP仍原异常 |
| 其余 P2 测试 | 默认不改，补独立高风险用例 | FalseResponse、wrapper None、正常返回身份、并发、认证清理 |
| P0/P1旧测试与 `test_api_contract.py` | 默认零修改 | 旧类型/对象、精确导出签名、旧HTTP/CLI行为 |

保留 P2 350 项及 P1 168 项的 nodeid/语义；若异常类型改变导致参数化 ID 改名，报告逐旧 nodeid → 新 nodeid、旧类型 → 新类型、发送次数断言映射，不删除/skip/xfail、不全局放宽为 Exception。`pytest.raises(RuntimeError)` 可能同时放过新子类，应明确断言具体类与字段，防止假绿。

### 9.4 最小变异检验（Build/Review 离线执行）

不引入第三方变异框架。使用独立禁网子进程，在 collection 完成、P1 guard 安装后仅替换内存中的目标生产函数；每个进程单一变异。正常 Kill Test 本身仍不 Mock 生产包装方法。

| 变异 | 必须被检出的测试及原因 |
| --- | --- |
| 在交易方法入口提前标记，或直接无条件转换 | K1 得到 Unknown 而非认证错误，失败 |
| 删除交易转换，只重新抛原异常 | K2 精确 Unknown 断言失败 |
| 转换仅包 POST，不包 JSON2/text | K3 类型断言失败 |
| 捕获交易失败后自动再调用一次实际请求链 | K2 交易计数/全事件序列失败，即使最后仍 Unknown |
| 捕获失败后自动 query_orders 或 login | K2 额外 POST/GET 失败，不只检查交易计数 |
| 去掉 allow_redirects=False | 307/308 内存 adapter 用例出现第二次 send 而失败；handler 首次redirect、第二次200，避免循环噪声 |
| 新异常改为 `raise ... from original` 或去掉 from None | traceback 秘密哨兵检查失败 |
| Status=-1 改为抛错、返回另一个对象或“拒绝”标记 | K4 返回身份/原始值断言失败 |

每个变异记录实际注入、目标 nodeid、命令、非零退出码和业务断言失败原因；语法错误/导入失败/挂起不算有效检出。恢复后相关正常测试通过，生产文件哈希/diff 无变异残留。若“移除保护”仍全绿，先修测试，不进入验收。

## 10. 如何证明不会自动重发

证据链必须同时具备：

1. **静态生产链**：公开交易方法 → 局部 helper → 真实 `_query_something` → 唯一 query POST → HTTP 检查 → 原结果解析；错误处理只构造异常，没有循环、递归交易、调用 login/query/cancel/create 的补偿分支。
2. **Session 层动态**：K1 区分认证/交易 URL；K2/K3 每次尝试恰好一个交易调用，完整 GET/POST 事件记录无其它调用；正常业务返回也一次。
3. **真实 requests Session 层动态**：仅恢复测试实例的原 request/send，所有 http/https 都挂纯内存 adapter；307/308 和传输异常均只进入一次 adapter.send。全局 P1 guard、OS 禁网保持。
4. **依赖前提核实**：默认全新 Session 的标准 adapter 重试为零，SDK 未安装 retry/auth-resend hooks；工厂继续受 P2 独占、可信、无隐藏重发契约约束。
5. **反证强度**：注入第二次交易或补偿查询的坏实现，相关测试必须红灯。

此证据证明受支持依赖配置下的 **SDK 单次调用不会自动重发**，不是互联网传输或券商 exactly-once、不是至多一次成交，也不能限制调用方再次调用或注入工厂内部任意重试代码。旧 API 的默认重定向行为不获得这一加强保证。

## 11. 文件修改范围（仅获批后）

| 文件 | 修改范围 |
| --- | --- |
| `src/emtl/errors.py`（新增） | 两个并列 RuntimeError 子类，安全字段/构造/消息，无第三方依赖 |
| `src/emtl/client.py` | 新客户端 HTTP 检查、私有交易 helper、局部标记转发、两交易方法接入、准确 docstring |
| `src/emtl/_protocol.py` | 仅 query 新增默认 None 的 on_post_start 参数及通知点；旧 check/结果解析不动 |
| `tests/test_trade_errors.py`（新增） | 异常字段契约、K1–K4、边界/额外HTTP/异常类别矩阵 |
| `tests/test_client_operations.py` | §9.3 明确预期变化、补非200/内存adapter/默认配置必要证据 |
| `tests/test_client_auth.py` | 仅新 HTTP 异常预期及字段；原失败清状态保护不变 |
| `tests/test_client_logging.py` | 两新异常消息/标准traceback安全、原日志保护 |
| `tests/test_client_concurrency.py` | 增加交易解码失败持锁及释放的确定性用例，不重写锁测试 |
| `docs/refactor/contracts/P3-trade-errors.md`（新增） | 批准后的字段/边界/不重发/安全范围与兼容差异 |
| `docs/refactor/contracts/P2-client-api.md` | 标注 P3 对新客户端失败语义的明确覆盖，链接新契约；保留历史范围说明 |
| `docs/reference/emtl.rst` | 增加 P3 契约下载链接，无真实执行示例 |
| `docs/refactor/plans/P3-plan.md` | 获授权后归档，追加批准/偏差记录 |
| `docs/refactor/reports/P3-acceptance.md`（新增） | 实测基线、红绿/变异、nodeid映射、Linux/Review/远端证据 |

有条件：`tests/client_helpers.py` 仅在现有内存 adapter/线程辅助确有不足时最小扩展；不得将业务判定藏入测试 helper。变异脚本可作为测试专用证据随报告记录，不新增生产基础设施。

默认不改：core、__init__、_coordination、const、utils、CLI、旧测试、根隔离设施、tox/pytest、workflow、Docker/驱动、依赖/发布元数据。现有驱动自动发现根 `test_*.py`，Docker COPY 已包含新增源/测试/docs，因此无需 CI 命名改造。继续使用 `dist/p1-offline` 容器报告目录，在 P3 报告中标明实际受测版本。

## 12. 分批实施、验收和回滚

所有步骤均以设计和实施批准为前提。先记录计划、再 Build；各批不自动 commit。

| 步骤 | 工作与独立验收 | 失败/停止条件 | 定向回滚 |
| --- | --- | --- | --- |
| S0 批准与实测基线 | 归档计划；核实§15批准项、HEAD/工作区、Python/依赖；禁网跑当前完整350项并保留JUnit/nodeids | 无批准、代码漂移、原套件失败、隔离不可用或真实凭证风险 | 无生产改动；保留失败证据，解决后再进入S1 |
| S1 错误契约与先行红灯 | 新错误模块与契约/Kill测试；不接入转换；契约可收集通过，K2/K3因正确原因红，K1/K4维持原保护 | 只能因导入错误失败、K1错误地容忍Unknown、无请求次数断言 | 定向撤本批骨架/测试，保留红灯记录；不弱化测试 |
| S2 新客户端HTTP与发送边界 | client独立_check_resp；query可选通知；真实认证/请求构造仍在标记前；更新仅HTTP预期 | 旧裸raise变了、认证失败被归Unknown、标记在POST之外错误时机 | 仅撤本批client/protocol片段，恢复对应新测试旧预期；旧core保持 |
| S3 交易未知闭环 | 接入_execute_trade及两交易；全传输/响应/双解析/text/FalseResponse；K1–K4全绿 | 任一Kill失败、改变成功返回、重复或补偿请求 | 回退本批接入到S2；保留故障案例，不扩API |
| S4 兼容、安全、锁与反证 | §9矩阵及旧套件；标准traceback/log；真实Session adapter；锁释放；逐项变异检出 | 秘密、旧行为变化、变异存活、线程未收束、假覆盖 | 仅修对应失败批次；变异仅子进程，验证源码无残留 |
| S5 完整离线证据 | 最终代码Linux --network none 三入口、tox合成环境、lint、JUnit/coverage/日志；旧节点映射 | runtime需联网、容器/报告失败、漏旧保护、镜像非最终源码 | 保留失败证据，修对应批次后重跑受影响检查；不关闭guard |
| S6 独立Review与远端收口 | 新独立Session审tracked/staged/untracked及证据；人类批准交付后核最终PR双workflow/artifact/tree | 确定缺陷FAIL；仅缺远端/独立证据NEEDS EVIDENCE | 回缺陷批次；已提交回滚需单独授权，定向revert |

回滚只撤销本阶段明确归属的 diff；不 reset --hard、git clean 或覆盖用户改动。发布后若回滚 P3 会恢复新客户端原始不确定异常行为，必须由维护者批准和告知调用方；不提供运行时兼容开关掩盖切换。

## 13. 可执行验证命令与证据清单

**以下均为获批 Build 待执行命令，本次未运行。** 默认 cwd 为仓库根。依赖准备与测试执行分开；执行期禁止联网。缺工具/系统隔离时停止，不退回无保护测试。

### 13.1 S0与局部验证

```bash
git rev-parse HEAD
git status --short --branch --untracked-files=all
.venv/bin/python -B -c 'import platform; from importlib.metadata import version; print(platform.python_version()); print({n: version(n) for n in ("pytest", "pytest-cov", "coverage", "tox", "requests", "urllib3")})'
```

不通过 import emtl 查询版本，以免初始化真实 OCR。macOS 先验证 sandbox 仅对 loopback 的 OS 阻断：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))'
```

预期 PermissionError/Operation not permitted；普通 connection refused 不是隔离证据。探针不可用则使用下节 Linux 容器。

Build 创建本次专用 `dist/p3-local` 后，先运行未改代码基线并留存 nodeid：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -vv --junitxml=dist/p3-local/baseline-junit.xml
```

新增文件后，各批按需执行，保存完整命令/输出和真实退出码；S1的预期失败单独记录，不混成最终失败：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_trade_errors.py -vv
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_client_auth.py tests/test_client_operations.py tests/test_client_logging.py tests/test_client_concurrency.py -vv
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_orders.py tests/test_core.py tests/test_auth.py tests/test_wrapper_contract.py tests/test_logging_safety.py tests/test_api_contract.py tests/test_cli.py -vv
.venv/bin/ruff check --no-cache src/emtl tests conftest.py
.venv/bin/black --check src/emtl tests conftest.py
git diff --check
git diff --cached --check
```

使用仓库固定 Ruff 0.4.1、Black 24.4.0；先核实版本。全量 tox、三入口和父凭证隔离由现有 Linux 驱动统一执行，不为 P3 新建另一套 runner。

### 13.2 Linux 完整系统禁网

依赖镜像构建允许准备网络，测试容器必须无外网。以下命令逐条检查退出码；使用本次唯一容器名，已占用时另取名，不能删别人容器。宿主先建 `dist/p3-linux`：

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p3-offline:local .
docker image inspect emtl-p3-offline:local
docker create --name emtl-p3-offline-run --network none emtl-p3-offline:local
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p3-offline-run
docker start --attach emtl-p3-offline-run
docker inspect --format '{{.State.ExitCode}}' emtl-p3-offline-run
docker logs emtl-p3-offline-run
docker cp emtl-p3-offline-run:/workspace/dist/p1-offline/. ./dist/p3-linux/
docker rm emtl-p3-offline-run
```

失败也先导出 inspect/logs/已生成报告再清理。应复用现有 workflow 的退出码/PIPESTATUS/EXIT trap 处理方式，不能因后续复制成功吞掉失败。最终需要精确断言 mode=none、容器退出0、报告非空且属于最终镜像。

驱动实际执行：独立 OS 探针 → tox commands_pre 合成父环境隔离 → 默认根完整 pytest/coverage → 仓库外不同顺序完整 pytest → 显式 tests 完整 pytest。默认报告路径虽名为 p1-offline，不代表本次仍是 P1 结果。

保存：构建命令/退出码/镜像ID/平台、最终生产测试文件哈希、NetworkMode、OS探针、容器退出码、收集状态、三份JUnit、coverage XML/JSON、versions.json、commands.json、tox-result.json、synthetic-environment.json、完整日志。三份JUnit节点集一致，未删/skip旧风险节点；不累计三轮数量为不同用例。不以覆盖率增长验收。

### 13.3 交付审查与远端

```bash
git status --short --branch --untracked-files=all
git diff
git diff --cached
git ls-files --others --exclude-standard
git check-ignore -v docs/refactor/plans/P3-plan.md docs/refactor/contracts/P3-trade-errors.md docs/refactor/reports/P3-acceptance.md src/emtl/errors.py tests/test_trade_errors.py
```

逐个读取 untracked 新文件；git diff 不包含它们。check-ignore 无匹配退出1正常，不是文件丢失。报告在 dist 被忽略时，应明确它是本地证据并交付索引，不能谎称已提交或上传。

远端只在维护者明确批准提交/推送/PR后核验：最终 `head_sha` 的 `build`、`Offline tests` 均成功；Artifact内核实三份JUnit、NetworkMode、退出码和日志。记录真实run/artifact URL/ID、event、conclusion。PR提交与merge提交不同则核对完整Tree或明确差异。在线docs linkcheck不是离线测试证据。

## 14. 风险、假设与阻断因素

| ID | 风险/假设 | 处置或证伪条件 |
| --- | --- | --- |
| R1 | 新客户端失败类型/对象变化影响调用方 except | 必须批准§7；不套用于旧API；发布说明明确 |
| R2 | 发送标记过早/过晚或跨调用共享 | 回调只在交易POST前、局部变量；K1/K2及粘滞标记测试必须检出 |
| R3 | 共享query的小改动影响旧裸raise上下文 | 旧check不动、无新增except包装旧路径；普通/活跃异常双契约 |
| R4 | 200假值响应与None混淆 | 保留FalseResponse/JSON None返回；缺失响应单独Unknown |
| R5 | catch Exception 会把程序/handler错误也归未知 | 边界后确实不能确认结果，保守接受；reason只说明阶段，调试详情损失明确 |
| R6 | 原异常context/frames仍驻内存 | from None仅保护标准显示；不承诺APM、locals、内存擦除 |
| R7 | 认证/查询/行情非HTTP原异常仍可泄漏 | 最小范围明确批准；要求全量脱敏则先重新规划，不伪称全覆盖 |
| R8 | 默认依赖/可信工厂可能隐藏retry/hook | 默认配置/实际版本审查与adapter测试；不支持带隐藏重发的工厂 |
| R9 | 异步中断/进程崩溃没有新业务异常 | BaseException原样；无Unknown不是可重发证明，不处理崩溃恢复 |
| R10 | 未设置默认请求timeout，锁可能长期占用 | 保留P2；本阶段不升级超时/重连/跨进程机制 |
| R11 | 当前实测350基线、最终Linux/远端/Review未执行 | S0/S5/S6明确门槛；缺证据NEEDS EVIDENCE |
| R12 | 真实Status、受理/成交/拒绝语义未知 | 原样返回，不抓实盘响应补证，不做自动确认 |
| R13 | 未知后SDK仍允许显式操作 | 维持READY及调用方控制，不等于自动恢复；不得静默引入断路器 |
| R14 | 新非整数HTTP状态拒绝是额外可观察变化 | §7单列批准；只为安全诊断，不扩展响应schema |

假设：仅批准 P3；P2 工厂独占可信、无隐式重发契约继续成立；运行时使用 Python3.11；所有测试材料合成且不需网络；现有账户锁不需改造。任一假设被推翻，暂停受影响步骤并修订计划。

## 15. 需要维护者明确批准的决定

2026-11-07：维护者在停止提示后回复“确批准计划”，确认整体批准以下 A1–A7。下列清单保留起草状态，以本段批准记录为准；不包含提交、推送、发布或代签独立 Review 的授权。

- [ ] **A1** 接受§5/§7两个异常的名字、并列RuntimeError父类、字段、三个reason值、状态码规则及新客户端逐场景类型/对象变化。
- [ ] **A2** 接受仅公开 `emtl.errors` 导入，不追加包级 `__all__`；旧九函数、CLI及core完全保留。
- [ ] **A3** 接受“session.post调用边界”保守语义、局部标记方案、Exception范围；BaseException中断保留。
- [ ] **A4** 接受 `raise ... from None` 的调试代价与标准traceback安全范围；认证/查询等非HTTP原异常保留，不能承诺全客户端脱敏。
- [ ] **A5** 接受200假值响应/JSON None的既有返回；非整数status在新客户端安全拒绝；不加券商业务状态解释。
- [ ] **A6** 接受未知后保持READY、不自动恢复且允许调用方显式只读查询；不提供自动确认或重发授权。
- [ ] **A7** 批准§11文件范围与§12实施步骤；当前保存计划不构成实施批准，切换Build并单独授权后执行。

旧API任何可观察变更、第三种异常/全局框架、包级新导出、BaseException改写、自动交易暂停/恢复、依赖/CI/timeout/retry修改，均须另行批准，不包含于上述默认方案。

## 16. 最终验收与停止条件

- [ ] S0真实完整基线通过，实施依据及审批可追溯。
- [ ] K1–K4正确；认证和交易POST逐URL计数；前置失败零交易，已尝试后普通失败统一Unknown。
- [ ] 非200安全字段/类型、JSON1/JSON2/text/None/非法响应矩阵满足；原正常返回和FalseResponse契约保留。
- [ ] 没有自动重试、补偿、重登重放、查询确认；真实Session adapter重定向测试及变异检出。
- [ ] SDK新异常str/repr/args与标准traceback、主动日志无合成秘密；安全保证没有越界夸大。
- [ ] 同账户整个交易/解码/转换持锁，失败后另一实例可继续；原账户隔离与异账户并行不回归。
- [ ] 旧九API/core行情/CLI、签名、导出、旧裸raise及原异常身份保持；350历史节点和168旧保护有保留或逐项批准映射。
- [ ] 最终代码Linux系统禁网三入口、tox凭证隔离、lint与完整Artifacts通过；无测试skip/弱化掩盖问题。
- [ ] 独立Review检查tracked/staged/untracked并PASS；最终远端双workflow及artifact/tree证据闭环。

出现重复交易POST、自动补偿/恢复、认证误归交易未知、令牌进入新异常标准traceback或SDK日志、跨账户污染、旧API意外变化、变异无法检出、隔离失效，立即 **FAIL** 并停止扩大实施。仅缺实测/远端/独立审查证据时为 **NEEDS EVIDENCE**，不能自评最终PASS。

全部验收满足后关闭P3、归档报告并立即停止；不扩展P4、真实协议验证、业务对账或订单确认自动化。

## 17. 本次 Plan 交付事实

已完成需求、契约、相关源码/测试/隔离设施/CI及历史收尾文档的只读分析；核实当前HEAD、分支、干净工作区、P2文档合并和生产测试树未变。

本次仅新增允许计划目录中的本文；已检查 Markdown 围栏、章节完整性、结尾换行和行尾空白，复核仓库仍无 tracked/staged/untracked 改动。未修改项目代码/测试/配置，未运行测试、真实OCR、任何账户请求或远端CI，未提交、推送或发布。下一步由维护者审阅§15；获准且切换Build后先归档，再按明确实施授权从S0执行。

## 18. 本次 Build 批准与执行记录（2026-11-07）

- §15 已记录维护者明确批准；起草阶段的待授权/未执行描述作为历史保留。开始 HEAD 仍为 `ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`，仅有未跟踪的本计划，无 tracked/staged 修改。
- S0：Python3.11.14；macOS sandbox 的 loopback 探针退出1、PermissionError/Operation not permitted；原套件350 passed（退出0），JUnit保存在 `dist/p3-local/baseline-junit.xml`。
- S1：新增 errors 与先行 Kill Test，无发送转换时4 failed/21 passed（退出1）；失败正好为K2两交易Timeout与K3 JSON2/text原异常未转换，不是导入失败。
- S2：新客户端 HTTP 检查与发送通知接入，先运行认证/查询及旧兼容集合，再接交易转换。
- S3：K1–K4和现有新客户端认证/业务/日志集合通过；S4补前置/响应/安全/锁/内存adapter矩阵及10种子进程内存变异，均被业务断言检出，生产源码无变异残留。
- 测试专用变异脚本归档于 `docs/refactor/reports/evidence/P3-local/mutations.py`（§11允许的测试证据）；原执行位置为忽略的 `dist/p3-local/mutations.py`，日志仍在该目录。交付报告记录注入方式与命令。未修改生产/测试隔离、依赖、CI、timeout、retry、core或导出。
- 最终完整测试、Linux及剩余证据状态以 [P3 实施报告](../reports/P3-acceptance.md) 为准；实施者自检不代签独立Review，不自动commit/push/发布。

## 19. 本地 Build 验证完成（2026-11-07）

- 最终macOS完整pytest/真实tox各442 passed；Linux系统级`--network none`三入口各442项，0失败/错误/跳过，真实tox凭证隔离与独立OS探针通过。
- P2基线350节点、P1历史168节点全部保留。10种内存变异均被业务断言检出，源文件SHA256无变异残留。
- Linux受测镜像`sha256:64018ba142237b257f386e88d1b73ed5ceec3b521d31aa2526158b5be9c683bd`，与最终受测代码/config46文件哈希一致；完整原始报告已导出`dist/p3-linux`。
- 无设计/API范围偏差；附带变异脚本和文档在构建后收口，不把它们冒称为镜像原件。S6独立Review与远端最终提交双workflow/Artifact证据仍缺，**NEEDS EVIDENCE，不关闭P3**。完整命令、风险与证据索引见实施报告。

## 20. 中断后续执行：任务状态与剩余工作

维护者要求按原计划继续未完成Build任务，保留已实现部分并优先补验证。本轮范围是核对实际代码/证据、补完整离线验证、更新进度与验收记录；不重复开发，不修改生产代码或测试，不把此续执行授权解释为提交/推送/独立Review代签授权。

| 原步骤 | 当前状态 | 本轮核实与剩余工作 |
| --- | --- | --- |
| S0 批准与基线 | VERIFIED | 批准可追溯；HEAD未变；原350节点完整保留 |
| S1 错误契约与先行红灯 | IMPLEMENTED / VERIFIED | 原21通过/4预期失败证据保留；现行契约与Kill Test通过 |
| S2 HTTP与发送边界 | IMPLEMENTED / VERIFIED | 实现哈希不变；本轮完整测试继续验证认证/交易分类及旧兼容 |
| S3 交易未知闭环 | IMPLEMENTED / VERIFIED | K1–K4与响应处理矩阵均通过；没有待补代码 |
| S4 兼容、安全、锁与变异 | IMPLEMENTED / VERIFIED | 本轮全套通过；10种变异证据与最终脚本哈希相符；Ruff/Black通过 |
| S5 完整离线证据 | VERIFIED | 46代码/config哈希与受测镜像相同；32份Linux证据哈希有效；三入口各442项且节点一致 |
| S6 独立Review与远端收口 | PARTIAL | 实施者tracked/staged/untracked交付自检已完成；以下两项仍PENDING，不得宣布P3关闭 |

S6剩余任务仍严格按原顺序：

1. **PENDING：** 新独立Session检查需求、批准计划、tracked/staged/untracked、源码与原始测试证据，形成独立Review结论；本Build不代签。
2. **PENDING：** 维护者控制提交/推送/PR后，核对最终head_sha的build、Offline tests、Artifact、NetworkMode、三份JUnit及合并Tree；本轮没有这些Git/远端操作授权。

本轮完整macOS sandbox测试退出0，442 passed in10.33s；代码/config、P1/P2节点及证据复核记录为`dist/p3-local/resume-verification.json`，测试日志/JUnit为`resume-tests.log`、`resume-junit.xml`。没有新发现的计划差异或未完成Build代码项。验收标准保持原§16，状态仍为NEEDS EVIDENCE。

## 21. S6 只读独立审查授权与执行安排

维护者在本次续执行中明确选择“授权只读独立审查”，允许启动一个新的审查子会话，独立检查需求、批准计划、全部tracked/staged/untracked改动及原始验证证据。此授权不包含提交、推送、发布、真实账户操作或远端workflow触发。

执行顺序：先保存本授权与安排；新子会话只读审查（不修改生产、测试或文档），给出PASS / FAIL / NEEDS EVIDENCE及证据；Build根据实际结论更新验收记录。若有确定缺陷，仅按原计划范围定向处理并重新验证；若只缺远端最终版本证据，则保持NEEDS EVIDENCE，等待维护者控制Git交付。现有S0–S5实现与验证不重复开发。

## 22. 独立Review R1限定修正方案（先记录，再Build）

独立子会话`ses_e4a54104dffeFedISc2HJcgid3`结论FAIL：HTTP200响应后的JSON/真实logging handler抛BrokerHTTPError时，原helper宽捕获错误分类为http_status。审查事实归档于[独立Review R1](../reports/P3-review-R1.md)。这是原§6.2伪代码与§5.1阶段契约的冲突；以已批准公开阶段契约为准，不新增异常或扩大API范围。

限定顺序：

1. 在现有test_trade_errors添加JSON1/JSON2、真实日志handler及撤单text抛BrokerHTTPError的公开链回归；确认旧实现因reason/status字段错误红灯，不接受导入错误假红。
2. 仅调整client._execute_trade：将query与结果处理分成两个捕获范围；仅query阶段特殊转换BrokerHTTPError；query正常返回后的普通Exception统一response_error/None。仍用局部attempted，前置失败裸raise，不捕获BaseException，保留旧wrapper接缝、双JSON、文本返回、账户外层锁和一次POST。
3. 运行定向及完整sandbox套件、全部10种反证与Ruff/Black；失败即定向修复，不弱化原断言。
4. 按原Dockerfile重建最终镜像，更新代码/config哈希，Linux --network none三入口及完整原始报告；旧镜像/证据保留为R1修复前历史，不冒充最终快照。
5. 新子会话独立复审R1及受影响范围；根据实际结论记录。远端仍等维护者控制提交/推送/PR，不自动执行。

额外文档仅归档首次独立意见与后续复审，属于S6证据。若需改变公开字段、旧API或引入新框架则停止另行审批；本修复不涉及这些变化。

### 22.1 R1 Linux准备失败及限定替代方式

原Dockerfile重建实际退出2：准备阶段从files.pythonhosted.org下载virtualenv时pip读取超时，尚未执行测试。原日志/参数/退出码保留`dist/p3-r1/docker-build.log`与`docker-build-result.json`，不冒称成功或测试失败。

分析：R1只改变client.py和test_trade_errors.py；依赖、打包、tox、CI与Dockerfile不变，首轮镜像已有完整已验证的Python3.11/tox环境。因此仅调整本地镜像准备方式，复用已核实的`emtl-p3-offline:local`（ID须等于`sha256:64018ba142237b257f386e88d1b73ed5ceec3b521d31aa2526158b5be9c683bd`），标准输入薄层Dockerfile仅COPY最终src/tests/docs，构建与测试均--network none，不重新下载或改变依赖。

必须核对新镜像RootFS完整基础层前缀与旧准备镜像一致，全部46代码/config哈希与R1当前受测源码一致，再执行原驱动三入口并导出全部原始报告。保留完整stdin、命令、退出码及两镜像inspect；若配置/依赖不一致或需运行期联网则停止。此为验证准备偏差，不改变生产或验收标准，也不替代后续最终提交的原CI构建。

### 22.2 R1本地修复验证完成，进入独立复审

4个回归先因字段分类错误失败，定向修复后相关219项通过；完整sandbox tox446项通过，10种原变异仍检出且无源码残留，Ruff/Black通过。禁网薄层构建退出0，最终镜像`sha256:b01c9f2ffbcb08826e5d99be4311bbb5bfc3dbc1ec84e390867199afa9f69dfd`，原15个依赖基础层完整保留；代码/config46文件与R1受测源码哈希一致。该镜像Linux --network none原驱动三入口各446项通过，OS探针/真实tox隔离/容器退出及报告导出均成功。

证据为`dist/p3-r1`与`dist/p3-r1-linux`；旧442项与首次构建下载失败记录保留历史。下一步由原独立Review子会话复审修复及最终原始证据，不由Build代签PASS。范围和原最终验收标准不变。

## 23. 独立复审完成与剩余收口任务

独立子会话`ses_e4a54104dffeFedISc2HJcgid3`复审明确：**R1关闭（当前快照）、源码/本地Review PASS；总体NEEDS EVIDENCE**。独立两次完整sandbox测试各446 passed，原handler反例与恢复旧宽捕获的四分支反证有效，10种原变异均检出，当前46文件与最终镜像及完整原始证据一致。结论归档[独立复审](../reports/P3-review-R1-followup.md)，首次FAIL记录不改。

| 原步骤/修复任务 | 最终本地状态 |
| --- | --- |
| S0批准/基线、S1错误契约及红灯 | COMPLETED |
| S2 HTTP/边界、S3交易未知闭环 | COMPLETED（含R1契约一致性修正） |
| S4兼容/日志/锁/变异 | COMPLETED |
| S5最终系统禁网三入口/原始报告 | COMPLETED（修复后446项、新镜像） |
| R1定向修复及独立复审 | COMPLETED |
| S6独立Review | COMPLETED，源码/本地PASS |
| S6最终提交远端双CI/Artifact/head_sha/Tree | PENDING，等待维护者控制Git交付 |

S6整体仍PARTIAL，不能关闭P3；没有待开发或未验证的生产代码项。归档后只做文档/范围/证据一致性检查，不重复开发。无提交/推送/PR/发布授权，不自动执行；远端最终原CI构建不由本地禁网薄层替代。最终验收仍严格为§16原条件。

## 24. 第二轮Review FAIL：HTTP状态来源定向修复计划

维护者明确授权仅修复交易HTTP状态来源识别。实查client.py与Review描述一致：query捕获BrokerHTTPError后使用异常status_code；_check_resp记录日志早于最终抛错。session.post或status getter抛BrokerHTTPError(401)会伪造http_status/401，真实503时日志handler的401也会覆盖真实状态。此前R1复审PASS为当时受审结论，保留不改；本问题单独记为R2 FAIL。

### 范围与实现

- 生产仅修改`src/emtl/client.py`，不改异常体系、公开API、core、共享_protocol或依赖/config；保留R1的query/结果处理分离。
- `_execute_trade`每次调用新增局部已验证非200状态（初始None）与仅赋值的回调；query异常只检查该局部值，绝不读取原异常类型/属性/消息判断HTTP状态。有已验证非200则http_status/真实值，否则exchange_error/None。
- `_check_resp`新增默认关闭的私有可选回调，只在本次Response.status_code读取成功且通过精确int检查、值非200后调用，且早于任何日志handler；随后保留原日志/HTTP错误路径。非法值/getter失败不通知。
- `_query_something`只在两项交易转发局部状态通知，通过本次调用局部check闭包接入，不使用self/global状态，不向认证/查询/行情传播交易观察；认证仍早于交易发送标记。
- HTTP200正常返回后的JSON/text/日志等处理仍response_error/None；无重试/补偿/自动确认，锁和READY/token规则不变。非交易与旧module API可观察行为保持。

### 分步验收

1. 仅通过真实create_order/cancel_order链，底层合成Session/Response/真实logging.Handler新增三场景×两交易：post抛401、getter抛401均exchange_error/None；实际503+handler抛401须http_status/503。每项检查post1/get0、READY/token、精确字段及全部SDK LogRecord脱敏；先在旧实现执行，必须6项业务断言失败。
2. 实现上述局部来源信号，运行新回归、既有阶段/认证/日志/并发/兼容集合，不改旧断言；补正常503/getter读取一次、非法状态不确立HTTP来源等有效保护。
3. 独立系统禁网子进程内存变异：恢复按异常类型/属性推断，须被新回归检出；将来源记录移到日志之后，须被真实503+handler失败检出。不修改被测分类函数以充当正常测试，只在变异进程临时替换生产函数。
4. 运行完整系统禁网pytest与真实tox、Ruff、Black、git diff --check；所有命令/退出码/节点与源码哈希留在新`dist/p3-r2`，旧证据不覆盖。
5. 更新验收报告追加R2事实、红绿、变异、文件范围与剩余风险。旧Linux446项及镜像明确不适用于R2修复后快照；本次没有新Linux/远端证据或独立复审时如实标记待证据，不沿用旧PASS。

停止条件：出现旧API变化、状态跨调用污染、异常类型推断残留、敏感日志、额外HTTP或非本缺陷生产修改即停止；不自动commit/push/merge，不真实交易，不扩大错误分类范围。

### 24.1 R2本地执行结果

6项指定回归在旧实现均因分类/字段失败，修复后定向265项通过；补两项读取一次/调用不污染回归后完整sandbox pytest与真实tox各454项通过（无失败/错误/跳过，历史350/442/446/168节点保留）。两项来源定向变异分别6/2业务失败，无collection错误；原10种变异也保持检出，变异后正常R1/R2集合12项通过。Ruff/Black（35文件）通过；最终范围/文档/源码一致性与diff检查在交付前核实。

生产修改仅client.py；测试仅test_trade_errors.py；新定向变异脚本为测试证据，计划与验收记录追加，不重写Review历史。全部新原始证据在dist/p3-r2；旧Linux和旧独立PASS不能签认R2当前快照。本地定向Build验证完成，第二轮Review FAIL独立关闭、修复后Linux及远端最终版本证据仍待后续，原验收标准不变。

## 25. 第三轮定向修复R3：安全HTTP错误不受日志Handler覆盖

维护者提供当前Review FAIL并授权仅修复非交易HTTP日志覆盖。实查当前_check_resp在验证非200及R2来源通知后直接logger.error，日志Handler的BrokerHTTPError(401)/ValueError会覆盖真实503，原异常消息/notes可进入标准traceback；与描述一致。既有R1/R2与原FAIL历史不改写。

### 限定实现与兼容约束

- 生产仅改`src/emtl/client.py::_check_resp`：成功读取真实status并通过原精确int验证、确定非200后，先构造安全BrokerHTTPError，再执行现有R2来源通知（仍早于日志），随后try记录固定HTTP日志。
- 仅捕获该logger.error调用的Exception并不传播其内容；不新增错误日志、不格式化/复制Handler异常，不读取其字段、不附加notes/cause。最后显式raise预先建立的安全错误from None，保护标准traceback显示。BaseException不捕获，必须原对象传播；不使用finally强制HTTP错误覆盖进程控制异常。
- 保持public BrokerHTTPError.status_code字段（维护者所指HTTP状态），不新增http_status别名、异常类或框架。R2交易局部来源、query/结果阶段分离、锁/认证/一次POST策略不改。
- 旧core、_protocol、errors、导出、CLI、端点/依赖/config不改。普通日志Handler异常被安全HTTP错误取代是本次明确授权的非交易失败语义修正，不扩展旧API全局处理。

### 测试和先行红灯

1. 在test_client_logging用真实TradingClient公共链、合成Session与真实logging.Handler覆盖验证码/查询/行情 × BrokerHTTPError(401)/ValueError的6场景。原Handler错误携带不同合成message/notes/cause；检查最终精确BrokerHTTPError/status_code503、str/repr/args/标准traceback及SDK LogRecord无哨兵、无原notes/cause显示、无额外请求、原状态/Session/Cookie策略。
2. 三路径Handler抛自定义BaseException必须同一对象传播；旧core公共查询在相同Handler故障下继续原对象传播（含普通/自定义BaseException），证明未全局改变旧HTTP行为。
3. 单独构造时序Kill Test以本地构造观察器记录安全异常建立事件、以真实Handler记录日志事件，要求先error后log。观察器返回真实BrokerHTTPError，不Mock分类函数，不替代上述6项真实链回归。
4. 实现前执行6项回归，须因原异常类型/状态/泄漏失败，不接受collection/语法错误假红；修复后运行全部新测试和R2交易来源矩阵。

### 变异、验证、交付

新测试证据脚本仅在collection后系统禁网子进程内变异_check_resp，至少检出：安全异常建立移到日志之后；重抛Handler；from Handler cause；拼接Handler消息；捕获BaseException吞掉。再检验把R2来源通知移入日志之后会被R2交易回归检出。旧R2文本变异脚本是当时快照的原件，保留不改，不以其结构匹配失败冒充检出。

运行完整禁网pytest与真实tox、Ruff/Black、git diff --check及P0/P1/P2回归（含旧API/CLI、R2来源测试），记录新dist/p3-r3，不覆盖旧证据。测试专用脚本归档docs/refactor/reports/evidence/P3-r3；计划/验收报告仅追加R3事实和结果。本次完成后停止，等独立Review；不启动代理审查、不自动commit/push/merge，不真实账户/交易，不扩P4；旧Linux/旧PASS不冒充新快照。

### 25.1 R3实际本地结果与停止

修复前6项真实链回归均因401错误字段或ValueError原消息/notes传播失败；限定修复后初次相关集合280项通过，最终完整sandbox pytest与真实tox各467项通过，无失败/错误/跳过，P1的168、P2的350与R2的454节点完整保留。5项指定错误实现分别检出1/6/6/6/3个业务失败；额外R2通知后移检出2项失败，无collection错误。变异后正常logging/trade_errors124项通过。

生产只改_check_resp；内存还原该片段后client.py与R2快照哈希完全一致，原R2交易方法字节保留；原logging测试仅新增imports/追加R3用例，旧断言字节保留。Ruff/Black（36文件）通过，旧core/CLI与一次POST/无自动重试保护继续通过。最终范围/文档/哈希/diff检查交付时保存dist/p3-r3/final-checks.json。

本次Build完成即停止，不自动启动Review。原FAIL与历史结果保留；等待独立复审和后续新Linux/远端证据，不把本地通过改称P3最终PASS。

## 26. 最终交付F1/E1限定修复计划

维护者明确说明交易生产代码及R1–R3功能Review已通过，当前FAIL仅涉及F1/E1交付阻断；本轮不改生产/测试/CI/依赖或异常语义，不重跑功能开发，不自动commit/push/merge。先完成F1门槛，再执行E1，最后交付核验。

### F1：脚本分类及完整文件质量门槛

实读`evidence/P3-final-linux/verify_host.py`和`observe.py`：前者断言固定本机ROOT、在自身目录写一次性run文件；后者固定/workspace与467节点、只观察原驱动。这些是一次性证据脚本，不是正式可复用工具。原计划§11只允许附带测试证据，未要求这两个脚本入库；该目录plan.md也明确不是新增CI runner。

1. 把两个脚本原字节移到Git忽略的`dist/p3-f1e1/tools/original/`，记录原/新路径、SHA256及既有host-commands/失败日志关联，不修写历史执行结果、不改原FAIL。新E1一次性驱动也只放dist工具目录。
2. 保存完整tracked/staged/untracked与源码哈希。检查全部候选交付Python；不放宽Ruff/Black或批量noqa。保留旧原始证据字节；如原始日志触发文本格式hooks，不修改日志以凑通过，而是保留带哈希的原字节归档并清晰排除临时工具。
3. 先在隔离的候选交付树（含全部untracked交付文件，使用其独立Git index，无commit）运行原配置`pre-commit run --all-files`，避免--fix污染交易代码；确认通过且字节不变后，在真实工作区同命令复核tracked范围。禁止仅利用--all-files漏掉untracked伪称通过。真实工作区/index保持原状态。
4. 缺pre-commit时仅准备验证工具，不改项目依赖/配置；F1未通过不进入E1。

### E1：最终467节点Linux完整证据

1. F1通过后重新记录完整候选清单，锁定源码/全部tests及fixtures、CI/config与非生成Docker COPY输入SHA256；与R3最终467节点基线对照，不修改测试凑数。
2. 当前工作区作context，原`ci/offline.Dockerfile`无缓存新构建、唯一tag/--iidfile；保存真实命令/退出码/日志/image inspect。构建准备可联网；不得以旧446/467镜像或COPY薄层替代。
3. 新建唯一--network none容器，无宿主挂载/账户环境注入；一次性observe代码及锁定manifest作为显式带哈希的验证附件复制到该新容器的独立工具目录，不变更镜像源码、原ci驱动或三个测试入口。复用原observer只观察run、每入口前后做原OS探针、即时解析JUnit，数量/节点/退出异常即停止。
4. 镜像读取输入哈希须与宿主锁定清单一致，测试前后再检查；原驱动三入口均467通过、无failure/error/skip，保存三份JUnit/coverage JSON/XML、tox版本与真实commands_pre凭证隔离。
5. 保存image ID/平台、NetworkMode、完整容器inspect/退出码、宿主执行/复制/清理状态；即使失败先收集原件，仅清理本次唯一容器，失败不能被后续成功吞掉。

### 最终交付

更新验收记录，明确旧446/467历史与本轮新467镜像结果；不改旧FAIL。完整原始证据存新dist路径，实际交付归档保留原字节并生成文件SHA256与归档SHA256索引；验证从归档解包后逐文件一致。明确待提交清单，临时脚本/缓存/工具目录不在其中；扫描候选文件及证据，不读取/输出真实凭证环境。复核全部tracked/staged/untracked、Ruff/Black/pre-commit/diff与源码不漂移。验收追加文档不冒称与测试镜像逐字节相同，代码/测试/CI必须相同。

停止条件：F1关闭；新Linux三入口通过；源码/镜像/原件/归档链路相符；最终文件清单无临时产物。若缺构建/隔离/报告证据则保持阻断，不放宽原标准、不继续交易逻辑或P4；远端最终提交双CI/Artifact/Tree仍须维护者控制交付后核验。

### 26.1 中断后继续执行（2026-11-08）

维护者确认按中断检查结果继续。已完成的两脚本原字节迁移、授权停止旧构建、25份原始材料归档不重复执行。其哈希已复核，46个生产/测试/config文件与R3快照一致；F1尚缺README/验收索引及完整候选树pre-commit门槛，E1尚未启动。

继续顺序不变：只更新索引和状态→完整候选质量门槛关闭F1→锁定新manifest/原Dockerfile新构建→原三入口及来源/隔离/退出核验→归档原字节证据和最终清单/扫描/质量复核。真实Git index不暂存或改写，交易源码/测试/CI/config保持保护哈希；缺证据则如实停止，不能拿历史结果替代。

### 26.2 本轮限定Build执行记录

F1完整候选门槛已通过；首次隔离copyfile丢失两文件执行位导致EXE001的FAIL原件保留，仅修临时工具为copy2，没有修改生产或质量规则。F1关闭后锁定95项COPY输入及467节点，原Dockerfile无缓存构建成功；新linux/amd64镜像2150b9bc9fe3的原三入口各467项、0failure/error/skip，7次OS禁网探针与tox预pytest凭证隔离通过。宿主及容器退出0，报告导出/清理通过；46文件R3保护快照不变。

122份F1/E1原件逐字节封装并逐成员SHA256核验；旧25份历史/原FAIL不改写。封装后的108文件完整候选树和真实工作区pre-commit、11个交付Python Ruff/Black、diff再次通过，静态模式和合成字面量核查无真实秘密发现；原件补充检查记录另封装，最终完整交付清单再复核。实际报告、边界和建议提交清单在P3-acceptance.md §13及evidence/P3-f1e1中。本轮完成后停止，不提交/推送、不进入P4；远端最终Git/双CI/Artifact/Tree和独立签认仍待维护者。
