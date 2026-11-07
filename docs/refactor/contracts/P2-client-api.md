# P2 TradingClient API 与安全边界

同步线程接口，目标运行时 Python 3.11。本文件描述客户端行为，不证明实际券商认证协议、会话有效性或真实交易结果。测试仅使用合成账户、内存 HTTP/OCR 替身及系统禁网。

## 最小公开接口

```python
from emtl import TradingClient

TradingClient(username: str, password: Optional[str] = None,
              *, session_factory=None, ocr_factory=None)
```

- `username` 必须显式指定，strip 后非空。身份在实例生命周期中不切换；仅 strip，不转小写、不删除前导零，不识别账户别名。
- `password=None` 时构造期间读取一次 `EM_PASSWORD`；显式字符串优先，显式空白不回退，缺失/空白凭证拒绝。不会读取 `EM_USERNAME` 选择账户。
- 构造不发请求；OCR 在首次实际识别时懒创建。环境后续改变不影响实例；换号或更改密码创建新实例。
- 凭证存在私有内存字段；不进入 repr、日志、锁键或自建异常。close 清除密码引用，不承诺 Python 内存安全擦除。

| 方法 | 返回与行为 |
| --- | --- |
| `login(duration: int = 30) -> Optional[str]` | 本次新非空 token，或认证证据不足时 None；处理/传输错误原样传播 |
| `query_asset_and_position()`、`query_orders()`、`query_trades()` | response 真值时原样 JSON，否则 None |
| `query_history_orders(size, start_time, end_time)`、`query_history_trades(size, start_time, end_time)`、`query_funds_flow(size, start_time, end_time)` | 历史字段 qqhs/dwc/st/et，JSON 原样返回 |
| `create_order(stock_code, trade_type, market: str, price: float, amount: int)` | 保留两次 JSON 求值，返回第二次结果；不解释业务 Status |
| `cancel_order(order_str: str)` | 输入 strip 后作为 revokes；返回 text.strip；不解释文本 |
| `get_last_price(symbol_code: str, market: str) -> float` | 自身 Session 行情访问，不自动登录；无效行情状态返回 NaN，价格转换/传输错误按既有规则传播 |
| `close() -> None` | 等待本账户当前操作完成，清认证/Cookie/密码引用并关闭 Session；重复安全；关闭错误传播但实例仍 CLOSED |

暂不提供上下文管理器、异步、logout、可换号 setter、token setter、统一异常层级或返回模型。

## Session / Cookie / OCR 所有权

每个实例独占 Session、Cookie jar、token 和 OCR。相同账户的两个实例也不共享认证态。

- `session_factory` 是零参数 callable，默认创建全新 `requests.Session()`；须返回全新、未关闭、独占的 Session 兼容对象，包含独立 cookies、get/post/close。
- `ocr_factory` 是零参数 callable，默认创建 `DdddOcr(show_ad=False)`；须返回独占且有 classification 方法的对象。
- 工厂返回资源由客户端拥有，Session 在 close 时关闭；OCR 无预设 close 协议，只释放引用。调用者不得并发使用或修改返回资源。
- 活动客户端复用同一 Session、jar 或 OCR 会被固定 ValueError 拒绝，不能关闭或清理另一 owner 的资源。构造失败释放本次已取得的独占资源。
- 不允许注入 `core.session`、已有账户会话、共享 adapters、自动 retry/auth-resend hooks；工厂是可信依赖，登记不能检测其任意隐藏状态/私自更换 jar。
- 未主动 close 的对象可被 GC，弱登记不永久保存历史身份；GC 不代替及时释放 Session 资源。

验证码、认证、token 获取、交易、查询和行情全使用自身 Session，不读写 `core.session`、`core._em_validate_key` 或旧 OCR。验证码 GET 保留 timeout=60，其它请求继续没有新增 timeout。

## 并发保证

单进程内，同一 strip 后用户名的所有存活 TradingClient 共用一条 RLock；覆盖认证、Cookie/token 更新、HTTP、response 真值判断、全部 JSON/text/价格处理及 close。内部自动 login 可重入，不会非重入死锁。

不同身份使用不同锁；短注册表锁不保护任何网络、OCR 推理或响应处理，因此请求可重叠。不同身份/密码组合的独立 Cookie/token 不交叉。

不保证锁公平性、CPU/OCR 吞吐线性提升、多进程/多设备串行、远端会话同时有效，或账户别名自动合并。调用方须统一同账户标识；无 timeout 请求可能长期占用账户锁。

## 新认证状态机

状态为 NEW / AUTHENTICATING / READY / FAILED / CLOSED。

1. login 在账户锁内先清旧 token/Cookie，再完整获取验证码、提交认证、解析 JSON。
2. 本地接受门槛为 JSON dict 的 `Status` 必须是 int 类型的 0（排除 bool、float、字符串）；才尝试本次 token GET，并要求正则提取出 strip 后非空 token。
3. 该门槛来自批准的保守本地规则；合成 0/-1 不代表已经核验券商成功/拒绝协议。缺失/未知响应视为证据不足，而非擅自解释错误码。
4. 不满足门槛、无 token 或空白 token 返回 None，进入 FAILED 并清 token/Cookie。传输、HTTP、OCR、JSON、text、加密异常也清状态并原样传播；新类不吞 KeyError。
5. NEW 首次认证业务调用自动 login 一次；没有 token 则固定 `RuntimeError("authentication required")`，业务 POST=0。FAILED 的后续业务调用不自动反复登录，需调用方显式 login 恢复。
6. READY 后业务异常不猜测为认证失效，不自动重登或重放；保留认证状态。FAILED 仍可读取不需登录的行情，但此前 jar 已被清空。
7. CLOSED 禁止所有 login/业务/行情方法，固定 `RuntimeError("client is closed")`，无 HTTP/OCR。

SDK 主动日志仅固定事件和 HTTP 状态码；不复制带 token URL、凭证、Cookie、完整响应或异常。原样传播的第三方异常可能自行含敏感信息，宿主打印它不在 SDK 日志脱敏保证中。

## 委托不确定时的边界

- 每次下单/撤单最多一次业务 POST 尝试；初次自动认证 POST 单独计数。
- 新客户端订单请求 `allow_redirects=False`，标准默认 adapter 不配置 retry；307/308 不隐式重发。
- Timeout、连接中断、响应丢失、HTTP 错误、解析失败、业务拒绝均不补单、不重试、不自动确认/补偿。异常可能表示请求已经受理，不能据此自动再次提交。
- 单次客户端发送不等于至多一次成交，也不证明真实券商接收状态。

## 旧 API 兼容与差异

原九项包级函数及 `core.get_last_price`、`emt`、`python -m emtl` 继续有效。`__all__` 仅在原九项末尾追加 TradingClient，原函数身份/顺序/精确签名不变。

旧认证仍独立环境回退、不解释 Status、无匹配保留旧 token、匹配空白写空 token、try 内 KeyError 返回 None；旧订单请求不静默新增 redirect 参数。新旧共用无状态协议细节，但不共用可变认证状态。

**旧 module API 是单个遗留上下文，不支持多账户并发切换；同账户旧 API 与新客户端混用不保证统一串行。** 旧登录失败/重定向风险不因新增客户端而自动消除；多账户调用方应只使用独立客户端。

## 使用结构（仅示意，不作为自动执行示例）

```python
client = TradingClient(username, password)
try:
    if client.login() is None:
        raise RuntimeError("authentication required")
    orders = client.query_orders()
finally:
    client.close()
```

自动测试必须注入合成 Session/OCR 工厂，禁止真实凭证及真实请求。
