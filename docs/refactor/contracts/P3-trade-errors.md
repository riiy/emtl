# P3 TradingClient 交易异常契约

本契约按批准的 [P3 计划](../plans/P3-plan.md) 覆盖 [P2](P2-client-api.md) 的部分**新客户端失败语义**。旧模块级九项 API、`core.get_last_price`、CLI、成功返回和包级导出顺序不变。只使用合成离线证据，不证明真实券商协议或成交结果。

## 公开类型

```python
from emtl.errors import BrokerHTTPError, TradeOutcomeUnknown
```

两类分别直接继承 `RuntimeError`，彼此无继承关系；不新增包级异常导出或公共异常基类。

| 类型 | 构造参数 | 稳定可读字段 |
| --- | --- | --- |
| `TradeOutcomeUnknown` | `operation: str, reason: str, status_code: Optional[int] = None` | 同名三个字段 |
| `BrokerHTTPError` | `status_code: int` | `status_code` |

`operation` 仅为 `create_order` / `cancel_order`。`reason` 仅有：

- `exchange_error`：已经尝试交易 POST，query 尚未正常返回时出错，包括 Timeout、ConnectionError、ChunkedEncodingError、响应 None/缺状态/状态读取失败/非整数状态。
- `http_status`：已读取到非 200 的精确内建整数状态，包括 3xx/4xx/5xx；`status_code` 为该整数。
- `response_error`：query 正常返回后，响应真值、JSON 第一次/第二次、订单固定日志、撤单 text/strip 等处理抛普通异常。

分类按实际阶段，不按异常类名反推阶段：query正常返回后，即使上述处理抛出`BrokerHTTPError`，也仍为`response_error`且`status_code=None`，不能把它的状态字段冒充本次交易HTTP响应。

其它 reason 的 `status_code` 必须为 None。HTTP 状态不接受 bool、float、str、int 子类或自定义对象，且不能为 200。operation/reason 仅接受精确内建 str 和白名单值。非法参数抛固定 TypeError/ValueError，不回显输入。不承诺异常序列化/冻结或完整请求诊断信息。

消息、args、默认 str/repr 仅使用固定文字、白名单值和安全整数。调用方按字段分类，不依赖英文消息全文。

## 发送边界不是成交证据

交易前置阶段包括 open/认证检查、验证码 GET/OCR、认证 POST、token GET、原表单/URL/headers/options 构造以及取得 `session.post` callable。这些步骤失败时不会把本次交易标为未知。

上述准备完成后、紧邻调用该 callable 前设置**本次调用局部**发送标记。从此开始的普通 Exception 保守转换为 TradeOutcomeUnknown。requests 内部序列化、URL 校验、连接失败也在该边界之后；不能凭异常类型断定“没有发出”。

| 阶段 | 对外结果 | 本次交易 POST |
| --- | --- | --- |
| 关闭、FAILED/无 token、输入 strip/请求构造失败 | 原异常 | 0 |
| NEW 自动认证失败 | 原非交易异常，或有效非 200 时 BrokerHTTPError；清 token/Cookie、FAILED | 0（认证 POST 单独计数） |
| 交易 callable 内/HTTP 检查失败 | TradeOutcomeUnknown(exchange_error/http_status) | 一次尝试 |
| 交易响应处理失败 | TradeOutcomeUnknown(response_error) | 一次尝试 |
| 正常完成 | 原 JSON / text.strip / 既有 None | 一次尝试 |

标记不保存于实例或全局，不能污染后续调用。整个 POST、解码和转换仍在原账户 RLock 内，异常退出释放锁。

**Unknown 只说明已尝试调用边界后无法确认结果，不证明数据包已送达、券商受理、成交或拒绝。没有 Unknown 也不普遍证明未提交。** KeyboardInterrupt/SystemExit/GeneratorExit 等 BaseException 继续原样传播；进程崩溃/外部中断不在转换保证内。

## 不重发、不解释、不自动恢复

- 每次调用最多一次 SDK 交易 POST 尝试；`allow_redirects=False`，不跟随 307/308 重新 POST。
- 不自动重试、重登后重放、补单、查询确认、撤销、对账、轮询或恢复。没有幂等键或 exactly-once 保证。
- 未知不主动清 token/Cookie 或改变 READY；HTTP 库正常 Cookie 处理不属于此“不主动清理”保证。
- 调用方可暂停自动交易并人工核对；仍允许另一次**显式**只读查询。查询不自动确认某次交易，也不是重发授权；不新增 SDK 断路器。
- 正常订单依旧两次 JSON 求值并原样返回第二个对象（含 Status=-1、list、None）；不解释业务 Status 或订单号。
- 撤单仍返回 text.strip，含 rejected/空串；status=200 的无异常假值 Response 继续返回 None、不解码。
- 底层 POST 实际返回 None 会在 HTTP 检查失败，归 exchange_error；不等同于上述假值响应或私有 wrapper None 测试接缝。

保证适用于默认 Session 和 P2 已约定的独占可信工厂、无额外 retry/auth-resend hook 配置。不保证工厂任意代码、调用方再次调用、互联网或券商侧至多一次成交。标准 adapter 重试预算为零，内存 adapter 测试不冒充覆盖 urllib3 的真实网络传输。

## 非交易错误与兼容差异

验证码/认证/token、六查询和行情的有效非 200，改为 BrokerHTTPError(code)，绝不标记 TradeOutcomeUnknown。新客户端状态存在但不是精确 int 时固定 `TypeError("invalid HTTP status")`；None/缺属性/状态 getter 抛错继续原异常。

| P2 新客户端原行为 | P3 行为 |
| --- | --- |
| 交易传输原 requests/其它 Exception | Unknown(exchange_error)，不保留原异常身份 |
| 交易非 200 的裸 raise | Unknown(http_status, code) |
| 交易缺失/非法状态响应的原异常或比较行为 | Unknown(exchange_error) |
| JSON1/JSON2/text/strip/真值/日志原异常 | Unknown(response_error) |
| 非交易非 200 的裸 raise | BrokerHTTPError(code) |
| 非交易非整数状态的比较/裸 raise/可能接受 | 固定 TypeError |
| 活跃 except 中新客户端 HTTP 错误可能重抛外层异常 | 安全新异常并抑制标准上下文显示 |
| 其余构造、认证证据不足、非 HTTP 认证/查询/行情、close/清理、BaseException | 保留 P2 原类型、身份及生命周期语义 |

完整逐场景差异以批准计划 §7 为准。旧 API 不获得这些新异常、安全字段、禁重定向或账户锁保证；旧普通/活跃 except 裸 raise、旧认证保旧 token 等行为保持不变。

## 脱敏范围与调试代价

SDK 不保存 request/response/原异常/URL/正文/凭证为新异常字段，不记录原异常字符串或增加主动错误日志；HTTP 只记录精确整数状态，订单日志仍是固定事件。

转换 `raise ... from None` 抑制标准 traceback 的底层 context/cause 输出；新异常的 str/repr/args 和**默认不显示 locals 的标准 traceback** 不复制合成秘密。原始异常中的 notes、嵌套 cause 也不进入该显示链。丢失原始错误细节是明确调试代价。

这不物理删除 `__context__`、frames/locals 或内存，不清洗第三方 APM、调试器、自定义格式器、主动遍历 context、宿主打印原异常或源码行内秘密字面量。

**非 HTTP 的认证、查询、行情等原异常仍按 P2 原样传播，可能含秘密，不承诺整个客户端 traceback 脱敏。** 新异常本身不授予重发许可，不替代人工风险处置。
