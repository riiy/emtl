# emtl P2：TradingClient 状态隔离与并发安全实施计划

## 0. 文档状态与执行授权

- 日期：2026-11-07；阶段：**P2 设计及实施已获维护者明确批准；按 S0–S7 分批执行**。
- 仓库保存位置：`docs/refactor/plans/P2-plan.md`。
- 起草来源：`/Users/lld/.opencode/plan/P2-plan.md`。起草时受 Plan 模式写入范围限制，仅保存于该目录；本次按维护者明确要求归档完整计划，未实施代码。
- 需求来源：`docs/refactor/requirements/P2.md`。
- 实施前须获得本计划的明确实施批准。仅归档计划的授权不等于批准设计或授权实施。
- 不自动提交、推送、打标签、发布或触发远端 workflow；不执行真实登录、查询、下单、撤单或真实 OCR 验证。
- 实施与测试目标运行时 Python 3.11；不引入 async、数据库、Redis、分布式锁、线程池管理器或复杂依赖注入框架。

本计划独立描述基线、设计、兼容边界、文件范围、测试、停止与回滚条件；执行者无需读取原聊天。

## 1. 实查基线与证据等级

### 1.1 Git 与本地文件

| 项目 | 本次只读核对结果 |
| --- | --- |
| 仓库 | `/Users/lld/emtl` |
| 分支 | `refactor/p2-client-isolation` |
| HEAD | `e35cf1782c4dded98fc4ce2ad3dce4c56648e28a` |
| HEAD 标题 | `Merge pull request #4 from riiy/docs/p1-acceptance-closure` |
| 本地 `master`、`origin/master` | 均指向上述 HEAD |
| 分支 reflog | 上述 SHA，`branch: Created from HEAD` |
| 工作区 | `?? docs/refactor/requirements/P2.md`；无 tracked/staged 修改 |
| `AGENTS.md` | 本地存在并已阅读；`git ls-files` 未列出，不假定远端存在 |
| `.opencode/commands/emtl-{plan,build,review}.md` | 本次路径搜索未找到 |
| 仓库 P2 计划 | 本次未发现已有目标文件 |

本次没有 fetch 或查询 GitHub，故上述 `origin/master` 只是实际读取的本地远端跟踪引用，不能声称已即时验证远端最新状态。Build 开始前由维护者确认基线是否仍适用；发生代码漂移先复核计划。不得覆盖或删除未跟踪的 P2 需求。

### 1.2 已阅读的依据

- 根 `AGENTS.md`；P0/P1/P2 需求；`docs/refactor/contracts/P0-public-api.md`；完整 P1 计划及验收报告。
- `src/emtl/core.py`、`__init__.py`、`const.py`、`cli.py`、`utils.py`。
- 根 `conftest.py`，全部根 `tests/` Python 文件与协议 fixtures，`pytest.ini`、`tox.ini`。
- `ci/offline.Dockerfile`、`ci/run_offline_tests.py`，四个现有 workflow；`setup.py`、`pyproject.toml`、API 文档页。

### 1.3 P1 回归基线与缺口

- P1 验收文档记载完整套件 **168 项**，本地及远端三种入口均通过；这不是本次 Plan 新跑的结果。
- 文档记录受测 SHA `8d0a2303d13a2f9d0c9aafae2f1bbe26bd2ade5d`，P1 合并 SHA `318fb45a5a279d103049c5adc1974e714847df4e`，二者树一致。
- 历史 Offline Run：`https://github.com/riiy/emtl/actions/runs/42199620264`；Build Run：`https://github.com/riiy/emtl/actions/runs/42199620359`；artifact：`https://github.com/riiy/emtl/actions/runs/42199620264/artifacts/13493921728`。
- 文档记载：NetworkMode=none、OS 探针成功、退出码 0、三份 JUnit 各 168 项；行覆盖 169/191，分支 35/40。只作为历史证据索引，不冒充当前 HEAD/P2 验收。
- P1 文档仍未提供最终独立 Review PASS 签认。允许完成本次 P2 设计；**开始 P2 Build 前应由维护者提供签认或明确确认接受该历史流程缺口**，不由本计划代签。
- 本次未运行 pytest、tox、lint、Docker、真实 OCR、远端 CI。Build S0 必须实际重跑基线；不得仅凭历史数量宣布当前可实施。

## 2. 当前调用图与必须保留的事实

```text
emtl.__init__：九个名称直接引用 core 同名函数
  login -> 环境回退 -> _get_captcha_code -> core.get / core.ocr
        -> core.session.post -> JSON 解析与格式化 -> _get_em_validate_key
        -> core.session.get -> 正则 -> 全局 _em_validate_key
  六查询 / create_order / cancel_order
        -> _query_something -> 复用全局 token 或 login()
        -> core.session.post -> _check_resp -> 包装层解析/返回
  core.get_last_price -> _query_snapshot -> core.session.get -> JSON -> get_float
emt / python -m emtl -> cli.run -> argparse -> exit(0)，不执行交易
```

| 源码位置（本次 HEAD） | 实际行为及设计约束 |
| --- | --- |
| `core.py:18–21` | 导入即创建 OCR、Session、空全局 token；新客户端不得使用这些可变对象 |
| `core.py:47–69` | 无 token 自动 login；tag 断言在 login 后；token 直接拼接；仅 `req_data is None` 使用默认表单 |
| `core.py:72–86` | 验证码使用模块级 `get`，timeout=60；OCR 真值转 int，转换失败递归；假值不转换 |
| `core.py:89–99` | 固定属性顺序正则、取首个匹配并 strip；无匹配不清旧 token；空白匹配写空串 |
| `core.py:102–138` | 环境回退早于 strip；不检查 Status；解析并格式化 JSON；只捕获 try 范围内 KeyError |
| `core.py:141–198` | 六查询检查 response 真值并原样返回 JSON |
| `core.py:201–233` | 下单两次 JSON，返回第二次；撤单输入/输出 strip；均无 SDK 自动重试 |
| `core.py:41–44` | HTTP 非 200 记录固定错误后裸 raise；通常为 `RuntimeError: No active exception to reraise` |
| `core.py:24–38`、`utils.py:34–37` | 行情异常状态 NaN；空白价格 0.0；缺字段/非法类型/传输错误按现状传播 |
| `tests/test_api_contract.py` | 精确锁定九项导出顺序、函数绑定、签名/注解；唯一批准的增量是末尾追加 TradingClient |
| 根 `conftest.py`、`tests/_offline.py` | collection 前清凭证、假 OCR、requests/socket guard；unconfigure 恢复 |
| `ci/run_offline_tests.py:93–107` | 第二轮按优先列表加 `test_*.py` 剩余文件，新增 P2 根测试会自动纳入三种入口 |

保持既有 endpoint、Host/Origin、字段名、字段类型、timeout 有无；行情 Host 看似不匹配也不顺手修复。`const._urls` 中虽有 `query_positions`，当前并无对应公开函数，本次不新增第七查询。

## 3. 首先设计并实施的最小 Kill Test

**Kill Test 是第一道实现门槛，不是计划阶段实际执行结果。** 先实现最小构造/状态/账户锁/真实 `query_orders` 路径，再验证；通过前不铺开全部业务 API，也不改旧认证。

测试文件：`tests/test_client_concurrency.py`；少量受控传输/线程辅助放 `tests/client_helpers.py`。仅用标准库 `threading.Event`、`Barrier`、线程结果队列及有限等待；不以 `sleep()` 或耗时比值作正确性依据。

### K1：同账户两个实例必须串行

1. 构造 `TradingClient(" P2_FAKE_A ", ...)` 与 `TradingClient("P2_FAKE_A", ...)`，注入不同 Session/OCR；初期允许测试设置两实例私有 token 为不同哨兵，随后补真实假登录链版本。
2. 先断言两个实例引用同一**生产账户锁记录**，而不是测试把两个独立锁改成同一个。
3. 线程 T1 调用真实 `query_orders()`，Fake Session 的 POST 设置 `first_entered` 后阻塞于 `release_first`。
4. 对原有共享 RLock 使用仅观测的测试代理：先真实 `acquire(blocking=False)`；失败时设置 `contended`，随后对**同一原锁**执行阻塞 acquire；成功时按原重入/释放语义转发。代理不增加一把串行锁、不替换生产锁选择算法。
5. 启动 T2 调真实查询，等待正向证据 `contended`；断言 T2 尚无发送事件。仅“线程已启动且短时间未发送”不够。
6. 释放 T1，等待两线程正常完成；断言请求事件顺序、临界区最大活跃数为 1、返回正确、锁最终可再次使用。
7. 参数化阻塞点：HTTP POST 内；HTTP 已返回后的 `response.json()` 内。第二种证明锁覆盖响应处理而非仅发送。

锁代理若未被进入、未出现真实竞争、线程不退出，均为失败，不能作串行成功。每个 Event/Barrier/线程 join 设例如 5 秒上限，仅用于失败检测；finally 释放阻塞点、收集所有异常并 join。CI 驱动的进程 timeout 作为最后兜底，不能让挂起线程被忽略。

### K2：异账户真正并行

1. A/B 使用不同账户锁记录、独立 Session、已知不同 token。
2. 两个 Fake POST 都先记进入事件，随后等待 `Barrier(2)`；屏障成功后再等待统一释放事件。
3. 主线程确认两者同时处于未结束的请求区间，最大活跃数为 2；释放并验证返回。
4. 若存在全局 HTTP 锁，第二个请求无法到达屏障，测试必须因屏障超时失败；不能因吞掉 BrokenBarrierError 变绿。
5. 此测试证明线程 I/O 路径可重叠，不宣称 CPU/OCR 吞吐随账户数线性提升。

### K3：Session、Cookie、Token 不交叉

1. A/B 的 Session 身份、Cookie jar 身份、token、Cookie/Authorization/header 哨兵、响应哨兵全部不同。
2. 与 K2 同步发送；断言每个请求只出现在自身 Session 记录、URL 只含自身 token、headers/Cookie 无另一账户哨兵，返回属于自身账户。
3. 使用真实 `requests.Session` 加每实例独立的纯内存 fake adapter，观察 `PreparedRequest.headers` 中实际生成的 Cookie，而不只检查 Fake Session.cookies。测试只在这些实例上替换被 guard 拦截的 send 为保存的 Session.send 并挂 fake adapter，所有可到达 scheme 都走假 adapter；不恢复全局 guard。该路径没有真实 transport。
4. 核对 `core.session`、`core._em_validate_key`、`core.ocr` 在新类操作前后身份/值不变；可将旧依赖替换成一触即错哨兵，证明没有偷用旧模块状态。
5. 初期 K3 可用预置私有 token；S3 必须再以每实例验证码 GET→登录 POST→token GET 的真实生产链获取哨兵，并扩展到下单/撤单。预置状态测试不能替代认证隔离验收。

**任意 K1/K2/K3 失败：停止扩大迁移。** 保留失败证据，修正共享锁或状态归属，再运行三项；不能跳过、xfail、放宽屏障或改用概率睡眠。

## 4. 架构比较与推荐

| 方案 | 成本与兼容风险 | 决定 |
| --- | --- | --- |
| 单一 TradingClient 实现 + 全部旧 API 委托默认客户端 | 需要切换绑定账户、保留旧 Session/Cookie/token、复刻旧 KeyError/None/空串/自动登录语义；还要迁移大量 module monkeypatch 接缝。安全策略标志会侵入新客户端 | 不选，当前失败语义冲突使总成本更高 |
| **实例化新客户端 + 小型旧状态/认证适配层 + 共享无状态协议函数** | 保留旧接缝与认证行为；新类负责实例状态和锁；共同的请求字段、token 正则和响应解码只有一份 | **推荐：满足约束且迁移风险最低** |
| 原 core 完全复制成第二套客户端 | 首次编码少，但之后字段/双解析/异常行为容易漂移，需要长期重复审计 | 不选，不交付两套不可校验的协议逻辑 |
| 仅 self.Lock 或一把全局业务锁 | 前者无法同账户跨实例串行；后者阻断不同账户并行 | 不满足硬性验收 |
| 固定数量分段锁 | 成本低，但不同账户可能碰撞，不能保证任意不同账户可并行 | 不选 |

### 4.1 模块和调用边界

```text
emtl.__init__
  ├─ 原九函数 -> core（旧凭证回退、旧状态、旧认证顺序和异常适配）
  │               └─ _protocol（无状态请求构造/发送辅助/响应解码）
  └─ TradingClient -> client（本实例状态、fail-closed 登录、生命周期）
                       ├─ _coordination（账户锁与注入资源所有权登记）
                       └─ _protocol（与旧 API 相同的无状态协议函数）

const / utils <- _protocol、core、client
```

- `client.py` 不导入 core 的 session/token/OCR，也不通过临时改写 globals 调用旧函数。
- `core.py` 不委托一个可切换账户的默认 TradingClient；旧模块仍是单个遗留上下文。
- `_protocol.py` 不保存 Session、Cookie、token、账户、OCR、默认客户端或可变响应缓存。
- 只提取实际共用的小函数：登录 headers/form（加密依赖作为明确参数传入）、token 正则提取、验证码识别流程、查询 POST、行情 GET、历史/订单/撤单表单、JSON/订单双 JSON/撤单 text/行情结果解码、HTTP 检查。
- 请求辅助显式接收 Session、token、检查回调等必要依赖。旧函数每次传入当时的 `core.session`、`core.login` 结果、`core.get`、`core.ocr`、随机数/加密依赖及 `core.logger`；不在默认参数或闭包中提前捕获 monkeypatch 接缝。
- 可保留薄包装的重复两三行控制流；不为消除所有重复引入 mixin、策略类、动态方法生成或通用执行框架。
- `_get_em_validate_key()` 保留旧状态赋值逻辑：共享提取函数返回 None 表示无匹配、空串表示空白匹配，不能把两者合并。
- 旧登录 JSON 格式化及 KeyError 捕获范围留在旧适配层；新类不同的候选认证规则留在 client。共同字段与匹配规则不复制。
- `_check_resp` 的旧函数入口、日志来源和裸 raise 语义保留；若实现移至 helper，传入原 logger，并验证活跃异常上下文下裸 raise 的行为也没有被新的 except 改变。

### 4.2 并发承诺的精确范围

同账户跨实例串行覆盖**所有显式绑定身份的 TradingClient 实例**。旧 module API 继续是单上下文兼容入口，不宣称支持多账户/并发切换；旧接口与 TradingClient 混用同一实际账户也不纳入统一串行保证。原因是旧接口可能从环境重新登录且无 token 时保留旧身份状态，无法在不改行为的前提下可靠推断账户。

该边界必须在 P2 文档及人工审批中明确；如果维护者要求“旧 API 与新实例混用也统一锁定账户”，则本方案停止实施，需先另行批准旧默认身份/换号语义设计，不能悄悄缩小承诺。

## 5. 新客户端最小公开接口

```python
class TradingClient:
    def __init__(self, username: str, password: Optional[str] = None,
                 *, session_factory=None, ocr_factory=None): ...
    def login(self, duration: int = 30) -> Optional[str]: ...
    def query_asset_and_position(self): ...
    def query_orders(self): ...
    def query_trades(self): ...
    def query_history_orders(self, size, start_time, end_time): ...
    def query_history_trades(self, size, start_time, end_time): ...
    def query_funds_flow(self, size, start_time, end_time): ...
    def create_order(self, stock_code, trade_type, market: str, price: float, amount: int): ...
    def cancel_order(self, order_str: str): ...
    def get_last_price(self, symbol_code: str, market: str) -> float: ...
    def close(self) -> None: ...
```

`Optional` 按项目现有注解风格使用，不因新文件改写旧函数注解。暂不新增上下文管理器、logout、token setter、可切换 username、统一错误类或配置对象；`close()` 加 try/finally 已足够。

### 5.1 身份与凭证

- `username` 必须显式传入 str；仅 strip 首尾空白，结果非空。错误类型为 TypeError/ValueError，固定消息不回显输入。
- 身份 key 为规范化用户名字符串，区分大小写，保留前导零与内部空白；不做 lower、整数化或 Unicode 合并。相同规范化用户名、不同密码仍共享同一账户锁。
- 新类不从 `EM_USERNAME` 选择身份；避免环境改变导致悄然换账户。
- `password is None` 时仅在构造时读取一次 `EM_PASSWORD`；显式 str 优先，显式空串/纯空白视为无凭证并拒绝，不再回退。非 str 拒绝。
- 保存规范化 username 与 strip 后密码于私有字段。密码只为后续本实例登录使用；不在锁键、repr、异常、日志中出现。close 清除密码引用，但不声称 Python 字符串能被安全擦除。
- 环境后续变化不影响已有客户端；更换账户/密码创建新客户端。新类没有 username/password 登录参数。
- 构造只创建本地对象、不发请求、不初始化真实 OCR；默认 OCR 在第一次验证码识别前于本实例账户锁下懒创建。

### 5.2 依赖接缝与资源所有权

- `session_factory`：零参数 callable，默认每次调用 `requests.Session()`；每个客户端构造只调用一次。工厂须返回全新独占 Session 兼容对象，含独立 cookies、get/post/close；不能返回 core.session 或已关闭资源。
- `ocr_factory`：零参数 callable，默认 `DdddOcr(show_ad=False)`；每个客户端第一次需要时调用一次。返回独占对象且有 classification 方法。
- 工厂结果所有权交给客户端：close 会关闭 Session；调用方不得同时使用/改写 Session、Cookie、headers、adapter 或 OCR。P2 不接受可共享的外部 Session 参数。
- 注入主要服务离线测试及简单定制；假工厂同样要求返回不同对象。检测活动客户端间复用 Session、Cookie jar 或 OCR 时，在新客户端发送前抛固定 ValueError；不得关闭/清空已归另一客户端所有的对象。
- 工厂是可信依赖，不承诺防御其任意代码、私下换 jar、共享 adapter 或重试 hook。支持的真实工厂须维持独占 adapters、无额外 retry/auth-resend hook；默认实现用标准新 Session，无自定义 retry。
- 共享注册表只记录资源身份和弱 owner，不存凭证/token；具体生命周期见第 7 节。测试验证重复活动资源被拒绝、原 owner 不受损、构造部分失败回收新资源。

### 5.3 返回、异常与生命周期

- 六查询 JSON 原样透传；下单仍两次 JSON 且返回第二次；撤单 text.strip；行情 float/NaN/异常与旧公共能力一致。
- 新 login 成功返回本次非空 token；保守认证判定不满足返回 None；HTTP/传输/JSON/OCR/text 处理异常在清状态后原样传播，不建立异常体系。
- 初次需要认证的业务调用可自动执行一次完整 login；若未得到 token，则固定 `RuntimeError("authentication required")`，业务 POST 为零。
- login 已失败后的 FAILED 状态，后续认证业务调用只抛固定 RuntimeError，不自动反复登录；由调用者显式 `login()` 恢复。
- 行情不要求登录，但必须走自身 Session 并持账户锁；失败登录后 jar 已清空，行情不得携带旧登录 Cookie。
- close 在账户锁下等待正在执行的操作完成，清 token/Cookie/密码引用、关闭自身 Session 并进入 CLOSED；重复调用无副作用。第一次 close 即使 Session.close 抛错也必须最终 CLOSED，原异常传播，重复 close 不再调用 Session.close。
- CLOSED 的所有业务/行情/login 方法固定 RuntimeError，零 HTTP。构造中途失败也不能漏掉新建且独占的 Session。
- 不主动打印第三方异常，不把异常文本嵌入新异常；原样传播的第三方异常本身可能含 URL/秘密，SDK 日志、repr 和 SDK 自建异常不复制它。宿主打印异常不属于脱敏保证。

### 5.4 文档示例（不自动执行）

```python
from emtl import TradingClient

# username/password 由宿主显式提供；自动测试必须用合成值及假工厂。
client = TradingClient(username, password)
try:
    if client.login() is None:
        raise RuntimeError("authentication required")
    orders = client.query_orders()
finally:
    client.close()
```

不把该示例写成会被 doctest 执行的真实请求。文档只展示读取操作，不安排实盘验证。

## 6. 状态所有权表

| 状态/资源 | 所有者 | 创建/变化/销毁 |
| --- | --- | --- |
| 新 Session | 单个 TradingClient | 构造创建；本账户锁下使用；close 一次；不从 core 取 |
| 新 Cookie jar | 该 Session/客户端 | 独立初始 jar；登录开始及失败清空；成功保存本次链 Cookie；close 清空 |
| 新 token | 单个 TradingClient | 初始空；登录开始清空；仅本次合格新 token 写入；失败/close 清空 |
| 认证状态 | 单个 TradingClient | NEW / AUTHENTICATING / READY / FAILED / CLOSED，见下表 |
| username、密码 | 单个 TradingClient | 构造规范化、绑定；密码 close 清引用；身份不可换号 |
| OCR | 单个 TradingClient | 懒创建、该账户锁内调用；close 释放引用；无假定的 OCR.close API |
| 请求 headers/form | 单次调用 | 从基础值复制，不修改 `_base_headers`；不缓存带 token 的 URL |
| 账户锁记录 | 同账户客户端共享 | 弱值注册表；客户端强持记录；实例消失后回收，不以密码作 key |
| 资源占用登记 | 进程内弱 owner 表 | 只用于拒绝活动 Session/jar/OCR 共用；close 或对象回收移除 |
| 全局注册表互斥量 | `_coordination` | 只保护极短查找/登记，无网络/OCR/响应解析 |
| 旧 session/token/OCR | core 遗留上下文 | 继续原生命周期和原认证行为；与新实例互不读写 |
| 默认 TradingClient | **不存在** | 不将旧 API 暗中切换到默认实例 |
| 环境变量 | 宿主进程 | 旧 login 每次按原规则读；新类仅构造读取密码一次；不写宿主环境 |

## 7. 锁设计、不变量及资源登记

### 7.1 最小实现

在 `_coordination.py` 定义一个可弱引用的小 `_AccountEntry`，只含一个 `threading.RLock`。使用 `WeakValueDictionary[str, _AccountEntry]` 加一把短生命周期访问用的模块级 `threading.Lock`：

```text
get_account_entry(normalized_username):
    在 registry_guard 下：
        查已有 entry；没有则创建并登记
        返回 entry（查到即有强局部引用）
```

每个客户端整个对象生命周期强持 entry，包含 close 之后：这样 close 与已等待的调用、新构造的同账户实例不会因删除锁产生两个并行锁。最后一个实例/执行中引用消失后 entry 由弱注册表回收。不要在 close 直接从账户表 pop，也不需要永久强引用缓存或手写引用计数。

资源所有权登记可用同一 `registry_guard` 下的 `WeakValueDictionary[int, TradingClient]`，key 为活动 Session、Cookie jar、OCR 的 `id()`，owner 为弱值。owner 强持这些资源期间 id 不会重用；close/构造失败释放资源前，先在 guard 内删除仍属于自己的登记。不得删除别人的登记，也不保留已释放对象的 id。对象未 close 但被 GC 后弱 owner 清除，注册表不无限增长。

Session 和 jar 在构造时原子检查后一起登记；OCR 懒创建后登记。工厂调用、Session.close、Cookie.clear、OCR 推理均在 registry_guard 外。若共享资源冲突，未取得所有权的资源不清理；已独占创建的其它资源按构造失败路径释放。GC 只保证表不永久缓存账户，不代替显式 close 释放 HTTP 资源。

### 7.2 获取顺序与覆盖区间

- 构造先通过 registry_guard 获取 entry，释放 guard 后创建/登记资源；不持 guard 等账户锁。
- 每个公开操作先 acquire entry.RLock，检查 CLOSED/认证状态，再执行整个操作，finally 释放。
- 临界区覆盖：自动/显式登录、验证码 GET 和 OCR、登录 POST、token GET 和 Cookie/token 提交、业务 POST、HTTP 检查、真值判断、两次 JSON 或 text.strip、行情 GET/解析、close。
- 内部调用 login 可重入同一 RLock；不另加 self.Lock，避免非重入死锁。
- 在账户锁内需要登记懒 OCR 时，允许短暂取得 registry_guard；反向路径永不等待账户锁，因此无锁顺序环。
- 不在 registry_guard 内发 HTTP、创建 OCR、等待 Event、解析响应、调用外部工厂/close。不同账户所有请求都在不同 RLock 上。
- 异常不吞、锁一定释放；同时测试 Timeout、JSON 第二次解析异常、失败登录之后同账户其它实例能完成。
- 不承诺公平性、取消等待、线程中断或跨进程锁。无超时的既有请求可能长期占用账户锁；P2 不升级 timeout 策略。

### 7.3 必须成立的不变量

1. 同一规范化身份的所有存活实例引用同一 entry，业务临界区不重叠。
2. 不同身份不因 HTTP/OCR 操作共用全局锁；短注册表互斥不是全局请求锁。
3. 每个实例独立 Session/jar/token/OCR；**同账户也不共享认证状态**，只共享锁。
4. token URL 在持锁后从本实例状态生成，并在持锁内消费响应。
5. FAILED/CLOSED 不得用旧 token 发送认证业务请求。
6. 注册表规模与存活/待操作对象有关，不随历史账户数永久增长；不打印注册表键。
7. close 不销毁另一个实例的资源，也不使仍存活的同账户实例取得不同锁。

## 8. 认证状态机与失败边界

### 8.1 新客户端的保守本地判定规则

新类在本计划审批后采用以下**本地接受门槛**：登录 HTTP 检查通过，JSON 是 dict，`type(payload.get("Status")) is int` 且值为 `0`，才继续获取 token；随后必须从本次 token GET 的 HTML 提取到非空 strip 后字符串，才进入 READY。

这不是宣称真实券商 `Status=0` 已经证实登录成功：0/-1 只来自现有合成 fixture。非零、缺失、bool、字符串、列表/null 等一律视为“认证证据不足”，清状态并返回 None；不翻译业务拒绝原因、不发明错误码。真实协议如果不满足该门槛，新类会保守拒绝；协议证据不足须交维护者决定，不放宽测试或用旧 token 兜底。该新策略属于本计划的明确审批项，旧 API 不套用。

新的验证码 GET 使用本实例 Session.get，保留现有 URL、headers 内容与 timeout=60；其它请求现有未设 timeout 的状态保留。验证码的有限非法识别递归、假值原样传表单保留，P2 不做算法/重试整治；这些动作都发生在订单业务 POST 之前。

### 8.2 新类状态转换

| 起点/事件 | 动作 | 终态/对外结果 |
| --- | --- | --- |
| 构造成功 | 独立空 jar、空 token；不联网 | NEW |
| NEW，首次认证业务调用 | 持锁调用一次 login(30) | 成功则业务继续；None 则 RuntimeError，业务 POST=0 |
| NEW/READY/FAILED，显式 login | 先令 token 空、状态非 READY，清 Cookie；再验证码→POST→解析 | AUTHENTICATING |
| 合格候选 JSON + 本次非空 token | 原子写本实例 token；保留本次链 Cookie | READY，返回新 token |
| JSON 可解析但不满足本地门槛 | 不发 token GET；清 token/Cookie | FAILED，返回 None |
| token HTML 无匹配/空白匹配 | 不回退旧 token；清 token/Cookie | FAILED，返回 None |
| 验证码/OCR/加密/POST/HTTP/JSON/token GET/text 任一步抛异常 | finally 失效化 token、清 Cookie；不得保留此前 READY | FAILED，原异常传播，包括 KeyError |
| READY，重复 login 后失败 | 不恢复之前 token/Cookie | FAILED，None 或原异常 |
| FAILED，认证业务方法 | 不隐式 login，不 POST | 固定 RuntimeError，仍 FAILED |
| FAILED，显式 login 成功 | 完整新认证链 | READY |
| READY，查询/下单/撤单发生传输或响应异常 | 不解释成登录失效、不重登、不重发 | 保留 READY/token，原异常；交易结果可能未知 |
| 非 CLOSED，行情调用 | 自身 Session、账户锁、不自动登录 | 认证状态不变 |
| 任意非 CLOSED，close | 等待当前操作；失效化、清理、关闭 | CLOSED；重复调用安全 |
| CLOSED，任意业务/login/行情 | 零 HTTP/OCR | 固定 RuntimeError |

实现宜用 token 清空 + 成功标志的 try/finally，保证异常和中断不会遗留 READY；不能在 except 内通过返回值吞掉原异常。支持的 Session jar.clear 不应失败；注入清理失败时至少 token 为空、状态 FAILED/CLOSED，保留原失败优先，不把清理异常写入敏感日志。

### 8.3 旧认证必须保持的差异

| 情况 | 旧 API 继续行为 |
| --- | --- |
| 空用户名/密码 | 分别从环境回退；纯空白显式值不回退，随后 strip |
| 登录业务 Status 非零/缺失 | 仍解析并格式化 JSON，继续 token GET |
| token 无匹配 | 返回 None，保留旧 token 和 Session/Cookie 状态 |
| token 空白匹配 | 返回空串并把旧 token 改为空串 |
| try 内 KeyError | 固定日志、返回 None；原 token 按既有执行点保留 |
| 其它失败 | 原异常传播；不主动清理旧认证态 |
| 无 token 自动 login 返回 None | 原 URL 拼接 TypeError，业务 POST=0 |
| 旧 login 改用另一 username | 仍使用旧全局 Session；不新增自动清 Cookie、不构建新默认实例 |

新旧策略不能通过一个默认客户端无条件共用。以上差异是本计划选择兼容适配层的依据。

## 9. 下单/撤单不确定响应的安全边界

1. 每次 create/cancel 调用的**业务 endpoint POST 至多一次 SDK 发送尝试**。初始自动登录 POST 单独计数，不与业务 POST 混淆。
2. Timeout、ConnectionError、ChunkedEncodingError、响应丢失、HTTP 非 200、None response、第一次/第二次 JSON 异常、text 属性异常都不触发重试、自动重登后重放、补单、自动查询确认或补偿撤单。
3. 合成业务拒绝 JSON/text 原样返回，不据此再次发送。异常不等同未提交，单次发送不等同至多一次成交。
4. **新客户端**下单/撤单显式 `allow_redirects=False`，防止 requests 对 307/308 隐式重发 POST；3xx 进入既有非 200 失败路径。默认 Session adapter 不配置重试。旧 API 调用参数保持原状，不默默加此参数。
5. 该新旧差异必须写入 API 文档及审批；原旧 API 一次 `session.post` 断言不能证明底层 HTTP 重定向没有重发，作为遗留风险保留。
6. Fake Session 层逐例断言一次业务 POST；另用内存 adapter + 实际 Session 路径，分别返回 307/308，断言只有一次 adapter.send、没有 redirect follow。不以 Mock.post 一次代替传输层重定向证据。
7. 构造的 fake POST 先记录“模拟已受理”再抛错，证明不会第二次调用；测试只验证客户端动作，不声称真实服务端受理状态。
8. 账户锁保护直到返回/异常传播前；测试响应解析阶段的并发竞争，避免下一次同账户操作看到尚未处理完的状态。
9. 不主动记录 URL、响应、请求正文、Cookie、Token、用户名、密码、验证码或异常 repr；新增错误仅固定文字。保留 P1 日志全部字段断言。

## 10. 旧 API 逐函数迁移与兼容证明

每行都保留包级函数直接绑定 core 原名称；生产签名、默认值和注解不改。对应新类方法除 self 外业务参数相同，login 单独绑定凭证。

| 旧精确签名 | 新类对应 | 旧层迁移与关键行为 | 必要证明 |
| --- | --- | --- | --- |
| `login(username: str = "", password: str = "", duration: int = 30) -> Optional[str]` | `login(duration: int = 30) -> Optional[str]` | 留 core 旧状态/环境/KeyError 控制流；只共用字段与 token 提取等无状态 helper | fallback、strip、完整顺序、JSON 格式化、无 token 留旧值、空白 token、Status 未解释、异常对象一致 |
| `query_asset_and_position()` | 同名 | 动态调用 core._query_something("query_asset_and_pos")，共享真值/JSON 处理 | tag、默认表单、原样对象、单次 POST |
| `query_orders()` | 同名 | tag=query_orders | 同上，含真实自动登录 |
| `query_trades()` | 同名 | tag=query_trades | 同上 |
| `query_history_orders(size, start_time, end_time)` | 同名 | tag=query_his_orders；qqhs=size,dwc="",st=start_time,et=end_time | 类型/值不强制转换；六查询错误矩阵 |
| `query_history_trades(size, start_time, end_time)` | 同名 | tag=query_his_trades；相同历史字段 | 同上 |
| `query_funds_flow(size, start_time, end_time)` | 同名 | tag=query_funds_flow；相同历史字段 | 同上 |
| `create_order(stock_code, trade_type, market: str, price: float, amount: int)` | 同名 | 共用订单表单/结果解码；旧 POST kwargs 不变；stock_code 不 strip；zqmc=""；两次 JSON/第二结果 | B/S、成功/拒绝、两次结果身份及各解析失败、异常原样、严格一次业务 POST |
| `cancel_order(order_str: str)` | 同名 | 共用 revokes 输入 strip、输出 text.strip；不 JSON 解析 | 空输入/失败文本/空文本、text 异常、一次 POST |
| `core.get_last_price(symbol_code: str, market: str) -> float` | 同名 | 共用 snapshot 参数与价格解码，旧用 core.session，新用 self._session | id strip、URL/headers、NaN/0.0、缺字段及传输异常、一次 GET |

其它保持：`core._query_something`、`_query_snapshot`、`_check_resp`、`_get_captcha_code`、`_get_em_validate_key` 的现有测试入口；utils 公共函数；CLI/console script。helpers 接收依赖时不把首次 monkeypatch 对象缓存成长期状态。

`__all__` 只在末尾追加 `TradingClient`。契约测试改为 `names + ["TradingClient"]` 的精确等式，仍逐个检查原九函数身份/顺序/签名；不改成宽松子集检查。`get_last_price` 仍不新增包级导出。

增加新旧请求/返回对照测试，直接比较两套实际调用记录，必要差异仅为：新验证码使用自身 Session、新登录门槛与失败清状态、新订单 redirect 参数、新生命周期/账户绑定。旧 P1 用例作为独立历史 oracle 保留，不能只让两套实现互相比较以掩盖共同回归。

## 11. P1 私有接缝逐项等价迁移表

本方案优先**保留原 P1 nodeid 和原接缝**，在新客户端补镜像用例；无需为了客户端重构整体改写 168 项。下表以实际函数名列出，所有已有参数化分支都保留。未来若确需改 nodeid，报告必须列出完整旧→新参数化映射，不能删除/skip/弱化断言。

| 原文件与测试函数 | 原接缝 → 新类接缝 | 不可减少的断言 |
| --- | --- | --- |
| `tests/conftest.py::_isolated_core`、`fake_captcha` | 原 core.session/get/ocr/token、SystemRandom 隔离保留；新增独立 client_factory fixture 注入每例 Session/OCR 工厂 | guard 先安装；每例清环境；新 fixture finally close，不清除仍存活的全局锁表来伪造隔离 |
| `test_core.py::test_login`、`test_login_fallbacks`、`test_login_malformed_json_propagates` | 原 core.session/加密/fake_captcha 保留；新 `test_client_auth.py` 用构造凭证与实例工厂、client 加密/随机依赖 seam | 旧独立 fallback、表单/strip/token、JSON 错误原样；新构造密码优先级单测，不把新规则替代旧用例 |
| `test_auth.py::test_false_ocr_is_sent_unchanged`、`test_empty_credentials_and_whitespace` | 原接缝保留；新 factory/OCR、构造校验 | 旧空/False/None/0 类型和 GET/POST 次数保留；新空凭证拒绝零网络另测 |
| `test_auth.py::test_rejected_login_still_extracts_token` | 旧 core token/session 保留；新真实 login 响应脚本 | 旧三种 HTML 结果和旧 token 保留；新拒绝响应即使另有旧 token 也失效且不 token GET |
| `test_auth.py::test_token_fetch_error_propagates`、`test_auth_failures_preserve_state_and_safe_logs` | 旧 Session/PropertyMock/加密保持；新独立 Session/token 初始状态 | 旧异常对象及旧 token 保留；新失败清状态/Cookie；日志所有字段无哨兵 |
| `test_auth.py::test_failed_auto_login_does_not_post_query`、`test_real_auto_login_then_query` | 旧真实公共链保留；新真实公共链 + 合格 Status fixture | 旧 TypeError/业务零 POST；成功两种 POST URL 顺序；新失败 RuntimeError/业务零 POST |
| `test_auth.py::test_captcha_failure_prevents_authentication_post`、`test_explicit_credentials_override_environment_and_preserve_request` | 旧 get/fake_captcha 保留；新 session.get/OCR factory | 验证码失败后认证 POST=0；完整 kwargs、请求次序、headers 不污染 |
| `test_core.py::test_queries` | 原 core.session/token/login spy 保留；新实例已认证 + login spy（仅验证“不调用”） | 六 API tag/字段、业务非零透传、单次 POST；安全端到端用例不 mock login |
| `test_core.py::test_auto_login_and_order` | 原 core.login stub 保留为委托包装测试；新另有真实假认证链 | 旧两次 JSON/第二结果/表单；原测试不升级宣称认证安全 |
| `test_core.py::test_cancel_order`、`test_order_exception_is_not_retried` | 原 Session/token 保留；新 Session 工厂与私有初始 token | strip、异常传播、一次 POST |
| `test_core.py::test_query_transport_error_propagates`、`test_query_invalid_response`、`test_explicit_empty_query_form` | 原 Session/token 保留；新实例请求 seam | 六查询全部参数、None/HTTP/JSON 失败、{} 不变默认表单、headers、异常对象与次数 |
| `test_core.py::test_non_200_preserves_bare_raise` | core._check_resp 入口保留；共享 helper 的实际调用 | RuntimeError 及固定日志；不换成 raise_for_status |
| `test_core.py::test_last_price`、`test_price_invalid_data`、`test_price_transport_error_is_not_nan`、`test_price_response_error_is_not_nan` | 原 core.session 保留；新 client Session 工厂 | NaN/0.0/缺字段/非法类型，原异常而非 NaN；完整 GET 参数和解析次数 |
| `test_orders.py::test_order_form_and_business_response` | 原 core.session/token 保留；新 client 工厂 | B/S×成功/拒绝、完整字段与类型、响应不重解释 |
| `test_orders.py::test_uncertain_submission_is_never_retried`、`test_bad_http_response_is_not_retried` | 原假 POST 实际调用链保留；新 client 假 POST | create/cancel 全异常矩阵、提交事件恰好一次、同一异常、POST 一次 |
| `test_orders.py::test_order_json_failure_is_not_retried`、`test_cancel_preserves_text_response`、`test_cancel_text_failure_propagates_without_retry` | 原 response.json/PropertyMock 和 Session 保留；新同类响应 | 第1/2次解析次数、第二结果/错误、text 读取恰一次、一次业务 POST |
| `test_wrapper_contract.py::test_wrapper_seam_none_returns_none_once` | 旧 patch core._query_something 保留；新 patch 实例._query_something | 仅证明包装层 None 返回与依赖一次，不计作 HTTP/无重试证明 |
| `test_wrapper_contract.py::test_false_response_traverses_request_chain_once`、`test_json_result_identity_is_preserved` | 原 Session/token/FalseResponse 保留；新实例 Session | 真正请求链、false 不解析、对象身份、双 JSON、POST 一次 |
| `test_logging_safety.py::test_no_sensitive_log_records`、`test_url_cookie_and_response_secrets_are_not_logged` | 原 core session/get/ocr/encrypt 保留；新完整实例链 | msg/args/formatted/exception fields 无秘密，不能只看 caplog.text |
| `test_logging_safety.py::test_captcha_invalid_ocr_recovers_without_leaking` | 原 core.get/ocr/SystemRandom 保留；新自身 Session/OCR/随机依赖 | 真正识别递归链、两次图片/随机数、timeout=60、固定日志；不能 mock 被测 captcha 方法 |
| `test_logging_safety.py::test_transport_exception_secret_is_not_logged`、`test_response_processing_failure_does_not_log_secrets` | 旧 Session/token/响应属性保留；新实例链 | 同一异常、实际一次 POST、全部 LogRecord 字段无秘密 |
| `test_api_contract.py::test_exports_and_signatures` | 只更新严格导出期望，追加新类签名单测 | 原九个绑定/签名/顺序、core/utils 签名全部保持 |
| 日志 root/CLI 用例、`test_cli.py`、`test_test_safety.py`、`test_offline_guard.py`、`test_offline_ci.py`、`test_fixtures.py` | 原接缝和用例不迁移；新增客户端导入/未配置依赖负向测试 | CLI 零交易、root logger 不改、启动前隔离/恢复、tox 凭证隔离、OS 禁网/失败码/artifacts 不退化 |

镜像用例集中在 `test_client_auth.py`、`test_client_operations.py`、`test_client_lifecycle.py`、`test_client_concurrency.py`、`test_client_logging.py`。复用 `response`、`protocol_cases`、`QUERY_CALLS`、`assert_no_sensitive_logs`，避免新框架。新旧认证差异用独立期望测试，不用一个“兼容模式”参数掩盖差异。

## 12. 完整新增测试矩阵

| 领域 | 场景及验收 |
| --- | --- |
| 构造/身份 | strip 后同账户同锁、不同密码同锁、不同规范化身份不同锁；前导零/大小写不合并；空身份/空密码/非字符串零网络拒绝；环境只读一次 |
| 资源隔离 | A/B及同账户两个实例 Session/jar/token/OCR 不同；外部活动 Session/jar/OCR 复用被拒绝且原 owner 未清理；工厂失败关闭已取得的独占资源 |
| 锁生命周期 | 并发首次构造同账户只能得到一个 entry；保留旧实例时 close+新构造仍同 entry；删除全部实例后 gc/weakref 确认 entry 可回收；多批合成身份不永久增长 |
| 最小并发 | K1/K2/K3；同实例多线程也串行；响应解析持锁；异常后锁释放 |
| 跨实例操作矩阵 | 同账户 login vs query、login vs create、create vs cancel；A 失败登录不会清 B 实例 token；异账户登录/请求可重叠；自动 login 嵌套 RLock 无死锁 |
| 认证 | 首次/重复成功；先成功后缺 token/空白/拒绝/无效 JSON/传输/HTTP/OCR/text 异常；候选 Status 类型矩阵；失败清 Cookie/token、不回退旧态；FAILED 业务零 POST；显式恢复 |
| 协议/返回 | 六查询、历史字段、空 dict 请求、业务拒绝/非 dict JSON 透传、FalseResponse/None seam、下单双 JSON、撤单 strip、行情异常与 NaN；新旧对照 |
| 资金副作用 | create/cancel Timeout/ConnectionError/ChunkedEncodingError/受理后丢响应/非200/None/JSON1/JSON2/text错误/业务拒绝；一次业务 POST、无其它补偿 endpoint；307/308 单 adapter.send |
| close | 重复 close 一次实际关闭、并发 close 等待请求和解码、close 异常最终 CLOSED、关闭后零网络/零 OCR；同账户其它实例继续可用 |
| 秘密 | login/查询/下单/撤单/HTTP失败/处理失败/repr/自建异常均不主动包含合成秘密；保留原异常身份，不记录异常 |
| 安全入口 | 根/显式/仓库外三入口全套、tox 实际隔离、导入前 guard、未配置新 Session/OCR 失败；Linux NetworkMode=none 和原 artifacts/失败清理机制 |

线程测试不在工作线程中调用 pytest fixture/monkeypatch，不在后台吞 AssertionError；线程结果/异常必须在主测试线程检验。线程全部结束后才 teardown/close/恢复依赖。资源生命周期测试只检查测试持有的 weakref 和前后增量，不清空生产注册表伪造释放。

## 13. 文件修改范围（仅批准后的 Build）

| 文件 | 计划动作 |
| --- | --- |
| `src/emtl/client.py` | 新增 TradingClient；实例状态、认证状态机、公开业务/close |
| `src/emtl/_coordination.py` | 新增共享 RLock 记录、弱注册表与活动注入资源登记 |
| `src/emtl/_protocol.py` | 新增实际共用的无状态协议/响应函数，避免完整复制 core |
| `src/emtl/core.py` | 保留旧函数/状态/认证适配及 monkeypatch 入口，仅提取共用逻辑 |
| `src/emtl/__init__.py` | 导入 TradingClient，__all__ 末尾追加 |
| `tests/client_helpers.py` | 新增小型独立假 Session/OCR 工厂、内存 adapter、并发观测辅助 |
| `tests/test_client_concurrency.py` | 新增 K1–K3、锁覆盖/生命周期/跨实例操作矩阵 |
| `tests/test_client_auth.py` | 新增凭证与失败状态机、完整认证隔离 |
| `tests/test_client_operations.py` | 新增业务/行情契约、无重发和重定向传输测试、新旧对照 |
| `tests/test_client_lifecycle.py` | 新增工厂/所有权/close/固定错误语义 |
| `tests/test_client_logging.py` | 新增客户端日志/repr/自建异常安全 |
| `tests/test_api_contract.py` | 只扩展精确导出和新类签名；原断言保留 |
| `tests/conftest.py` | 增加独立 client_factory fixture/teardown；原 core fixture 保留 |
| `tests/test_test_safety.py` | 仅增加新类未配置依赖/导入负向验证 |
| `docs/refactor/contracts/P2-client-api.md` | 新增本计划批准后的新 API、认证门槛、并发/混用/重定向/生命周期说明 |
| `docs/reference/emtl.rst` | 最小增加 P2 契约链接/类文档，不改旧契约内容 |
| `docs/refactor/plans/P2-plan.md` | 本次已归档；实施获批后追加偏差与执行记录，不倒填结果 |
| `docs/refactor/reports/P2-acceptance.md` | Build/Review 实际证据、nodeid映射、风险和 CI 索引 |

原 P1 测试默认不改；若 helper 提取实际暴露私有依赖捕获问题，优先修实现保持 seam，不批量改测试迁就实现。只有经逐项记录、风险断言等价的必要 seam 调整才可修改对应原测试文件。

现有 Dockerfile 自动 COPY src/tests/docs；CI 驱动自动发现根 `test_*.py`。**预计无需修改 workflow、tox、Docker、网络 guard 或 CI 输出路径。** 沿用 `dist/p1-offline` 和 artifact 名作为既有设施，在 P2 报告注明其含本次 P2 结果；不为了命名做全套 CI 重构。

不纳入：const endpoint 改动、utils 公共行为、CLI、setup/python_requires、依赖版本、打包/发布、P0/P1 历史证据。`setup.py` 仍声明 >=3.10、release workflow 仍用3.10、formatter target py38；P2 以3.11验收，元数据迁移另行批准。

## 14. 分批 Build 顺序、验收与回滚

依赖：S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7。每批通过后才继续；批次不意味着自动 commit。

| 步骤 | 最小工作与文件 | 通过门槛 / 失败停止条件 | 定向回滚 |
| --- | --- | --- | --- |
| S0 批准/基线 | 核对已归档计划及实施批准；记录 HEAD/状态/版本/P1签认；在离线环境跑原全套 | 实际基线通过、分支和用户文件归属明确；漂移/真实凭证/guard异常立即停 | 仅撤本次记录，不动用户 P2 需求；无生产变更 |
| S1 最小垂直切片与 Kill Test | 新 client/coordination、构造独立 Session/token、共享账户锁、真实 query_orders；K1/K2/K3；暂不包级导出完整类 | 三项均通过；解析阶段也串行、异账户同时进入；任一失败不扩业务 | 仅撤新增切片/测试本批 diff，保留失败记录，旧 core 不受影响 |
| S2 所有权/生命周期 | 工厂独占验证、OCR懒创建、弱表回收、close；补异常释放和同账户新构造测试 | 无资源交叉/锁分裂/永久缓存；关闭/部分失败无泄漏；K1–K3继续通过 | 定向撤本批新类部分，回 S1；不删已有安全断言 |
| S3 实例认证 | 新 login/NEW-FAILED-READY-CLOSED、session验证码；提取必要纯协议 helper；旧认证控制流保留 | 完整认证隔离/先成功后失败/旧token保护；原 auth/logging 回归；未知 Status 不误判成功 | 回退新认证/提取片段，恢复原 core 对应片段，保留失败证据 |
| S4 新业务能力 | 六查询/历史/行情/下单/撤单；共享纯业务逻辑；新订单禁redirect | 逐API完整字段/返回/异常；一次业务POST和adapter.send；跨实例订单/解析持锁 | 撤本批业务方法及对应 helper 提取，已通过独立切片可保留未发布 |
| S5 旧兼容收口与导出 | core 薄包装共用逻辑；逐函数对照；包级追加类；API文档 | 原168保护继续通过，仅批准的__all__增量；无签名/网络kwargs/失败语义变化 | 恢复对应旧包装实现和导出，不删原测试/日志防护；禁止将新 fail-closed套给旧接口 |
| S6 全量离线/质量 | 三种入口、不同进程顺序、tox、lint、Linux完整禁网；生成证据 | 所有风险矩阵通过、OS证据/report齐全；执行期要求联网/挂起/丢报告立即停 | 修对应批次，不关闭guard或缩减矩阵；证据失败保持失败状态 |
| S7 独立Review/交付 | tracked/staged/untracked全审，报告与远端CI核对 | 最终版本远端CI、独立Review PASS；仅缺证据为NEEDS EVIDENCE | 退回缺陷对应批次；已提交内容回滚需另获授权，不reset/clean |

任何阶段发现旧 API 可观察变化（包括登录失败、请求次数、URL/kwargs、响应处理次序、CLI），停止并单独提请批准。不得靠删旧测试/改预期将其隐藏。最终批准方案若改变第4、5、8、9节，先修订计划再继续。

## 15. 验证命令与执行证据

以下命令是 **Build 待执行清单**，本次 Plan 未执行。预装依赖后测试断网运行；缺依赖在准备阶段解决，执行期失败不能临时联网补装。

### 15.1 基线与局部测试（macOS 已有环境）

工作目录仓库根；先确认 Python 3.11 与依赖版本，版本查询不要 import emtl 初始化真实 OCR。

```bash
.venv/bin/python -c 'import platform; from importlib.metadata import version; print(platform.python_version()); print({n: version(n) for n in ("pytest", "pytest-cov", "coverage", "tox", "requests")})'
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -q
```

先验证本机 sandbox 能实际阻止 loopback socket（只用127.0.0.1，不访问真实服务）；若不可用，改在下述 Linux network-none 容器执行，不把普通 pytest 说成 OS 禁网。

各文件出现后按批运行：

```bash
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_client_concurrency.py -vv
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_client_lifecycle.py tests/test_client_auth.py tests/test_auth.py tests/test_logging_safety.py -vv
PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_client_operations.py tests/test_client_logging.py tests/test_core.py tests/test_orders.py tests/test_wrapper_contract.py tests/test_api_contract.py tests/test_cli.py -vv
```

完整 tox 在准备好的 py311-cover 环境运行，创建 `dist/p2-local` 后输出证据；设置合成父凭证以验证真正 commands_pre：

```bash
PIP_NO_INDEX=1 TOXPYTHON="$PWD/.venv/bin/python" EM_USERNAME=P2_FAKE_USER EM_PASSWORD=P2_FAKE_PASSWORD EM_P2_SENTINEL=P2_FAKE_VALUE NETRC=P2_FAKE_NETRC SSH_AUTH_SOCK=P2_FAKE_SOCK SSH_AGENT_PID=P2_FAKE_PID sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p2-local/tox-result.json -- python -m pytest --cov --cov-report=term-missing --cov-report=xml:dist/p2-local/coverage.xml --cov-report=json:dist/p2-local/coverage.json --junitxml=dist/p2-local/junit.xml -vv
```

根默认入口、显式 `tests/`、仓库外完整入口由 Linux 驱动再验证；不为测试顺序引入第三方插件。新并发用例至少出现在完整三轮结果中，不能只跑局部证明稳定。

### 15.2 Linux 系统禁网

依赖镜像构建允许联网；执行容器必须 `--network none`。继续使用现有 `ci/run_offline_tests.py`，自动跑 OS 探针、tox/环境隔离、三入口完整套件、覆盖率与报告。

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p2-offline:local .
docker create --name emtl-p2-offline-run --network none emtl-p2-offline:local
docker inspect --format '{{.HostConfig.NetworkMode}}' emtl-p2-offline-run
docker start --attach emtl-p2-offline-run
docker inspect --format '{{.State.ExitCode}}' emtl-p2-offline-run
docker logs emtl-p2-offline-run
docker cp emtl-p2-offline-run:/workspace/dist/p1-offline ./dist/p2-linux
docker rm emtl-p2-offline-run
```

容器名占用时使用唯一名称，不删除不明已有容器。复制前创建宿主输出父目录；即使测试失败，也应先收集 inspect/logs/report 再清理。必须精确验证 mode=none、容器退出码0、所需报告非空；不能以 docker start/上传成功判定通过。优先沿用现有 workflow 已测试的 EXIT trap/PIPESTATUS 处理，不另写简化失真版本。

必留证据：镜像ID/平台/基础镜像信息、构建结果、NetworkMode、独立OS探针、container exit code、host-status、三份JUnit、coverage XML/JSON、versions.json、commands.json、tox-result.json、synthetic-environment.json、完整日志。P2验收报告说明既有容器路径仍名为p1-offline，不能误引用旧运行文件。

### 15.3 静态与交付审查

```bash
.venv/bin/ruff check --no-cache src/emtl tests conftest.py
.venv/bin/black --check src/emtl tests conftest.py
git diff --check
git diff --cached --check
git status --short --branch --untracked-files=all
git diff
git diff --cached
git ls-files --others --exclude-standard
git check-ignore -v docs/refactor/plans/P2-plan.md docs/refactor/contracts/P2-client-api.md docs/refactor/reports/P2-acceptance.md
```

使用项目既有固定工具版本（P1记录 Ruff0.4.1/Black24.4.0，实施时核实）。逐个读取新文件，不能只审 git diff；check-ignore 无匹配退出1是正常。自动格式化若修改文件需重新审查/验证相关集合。

### 15.4 远端验收

维护者批准并自行控制提交/推送/PR后，核验最终提交对应的 Offline及原必需Build/check/docs jobs。记录真实run URL、event、head_sha、conclusion、artifact URL/ID和内容。若PR受测SHA与合并SHA不同，核验完整Git Tree或实际代码差异，不能用历史P1结果替代P2。

P2报告逐项对应第12节风险矩阵与实际nodeid/命令/退出码。覆盖率与数量只观察，不作为隔离或无重发证明。远端未执行或artifact缺失即NEEDS EVIDENCE，不宣称PASS。

## 16. Review 清单与最终验收

- [ ] Git基线、计划批准、新客户端行为差异批准及P1历史签认状态清楚。
- [ ] 新旧调用图与实际实现一致，没有临时换globals、共享Session/token/默认可切号客户端。
- [ ] K1同账户跨实例及解析阶段串行；不是仅self.Lock或未调度的概率测试。
- [ ] K2异账户两请求实际同时停留在临界区；无全局HTTP/OCR大锁。
- [ ] K3 URL、PreparedRequest Cookie/headers、Session、token、返回值无交叉；完整假认证链也验证。
- [ ] 弱锁表/资源登记无永久历史增长、close后无锁分裂、异常后可继续操作。
- [ ] 新登录失败清旧token/Cookie并阻止认证业务；旧登录失败特征和异常传播保持。
- [ ] 所有旧签名/顺序/函数绑定/字段/返回/CLI不变；__all__只追加TradingClient。
- [ ] 旧P1全部风险断言有保留或逐nodeid等价映射，无删除/skip/弱化；mock边界正确。
- [ ] 每种下单/撤单不确定响应均一次业务POST；新客户端307/308不会隐式再次发送；没有补单/补偿/重登重放。
- [ ] 主动日志、repr、自建异常无敏感字段；不夸大第三方原异常的脱敏能力。
- [ ] 根、显式、仓库外入口、tox凭证隔离、guard生命周期及Linux系统禁网完整通过。
- [ ] tracked/staged/untracked与被忽略交付物均已检查，证据对应最终实现版本。
- [ ] 最终远端CI及artifact可核验、独立Review为PASS。

Review结论：确定的状态交叉/重复发送/兼容性/挂起缺陷为FAIL；只缺最终远端证据为NEEDS EVIDENCE；满足全部约束才PASS。达到上述门槛即停止P2，不扩展P3/P4技术债。

## 17. 风险、假设、审批点与阻断

| ID | 风险或未决事实 | 处置与边界 |
| --- | --- | --- |
| B1 | 计划已获授权归档，但设计与实施未获批准 | 本次只保存文档；明确批准设计及实施后才可执行 Build |
| B2 | P1文档无最终独立PASS签认 | Build前维护者补充或明确确认历史流程缺口；不阻碍本次设计，不代签 |
| B3 | 本地origin/master未即时远端核验 | 维护者确认最新基线；漂移时先重新分析，不自动fetch/切分支 |
| A1 | 新Status接受门槛仅据合成样本，非真实协议证据 | 本计划批准才实施；未知响应保守失败；不得宣称券商认证协议验证完成 |
| A2 | 并发承诺限显式TradingClient，不覆盖旧新同账户混用 | 文档明确并审批；若要求混用串行，先另行设计旧身份管理，暂停该方案 |
| A3 | 新类仅构造时密码环境回退、FAILED需显式恢复、订单禁redirect | 新增API的明确行为；旧接口不套用；批准前不Build |
| R1 | 同实际账户可能有多个别名/资金号 | 仅按strip后字符串识别同账户；无证据不合并别名，调用者须统一标识 |
| R2 | 同账户不同Session登录可能在券商端互相失效 | 锁只防本进程并发，不保证远端多会话有效；本阶段禁止真实验证/自动恢复 |
| R3 | 旧API保留旧token、Cookie、Status未解释及默认redirect | 已知遗留风险，P2兼容约束下保留并测试，不能声称旧API获得新安全保证 |
| R4 | Session工厂/hook可能自带隐式重试或共用底层对象 | 支持契约明确独占无重试；默认Session验证adapter/redirect；不防任意可信注入代码 |
| R5 | OCR每实例内存开销、递归识别与无timeout请求 | OCR懒创建减成本；保留现状且标注锁长时间占用风险，不借P2升级策略 |
| R6 | Cookie清空后协议是否仍兼容、captcha改用Session | 新类明确边界且保持URL/timeout/字段；合成测试不证明实盘协议，缺证据不得放开自动实测 |
| R7 | 订单异常不能确定服务端是否受理 | 原异常/响应传播、禁止重试/补偿；只保证调用层至多一次尝试，不承诺成交唯一性 |
| R8 | 弱注册表回收与close并发容易拆锁 | 强持entry至对象生命周期结束；正向竞争/新构造/回收测试必须通过 |
| R9 | 原异常可能携带秘密，Python内存不可安全擦除 | 不主动记录/复制；固定自建异常；仅清引用，不作超出实际能力保证 |
| R10 | 本次没有运行当前基线或P2测试 | S0实测及后续Linux/远端证据是门槛，历史168不代替验证 |
| R11 | 打包声明>=3.10与目标3.11仍有差异 | P2不改无关发布元数据；如审批要求同步最低版本迁移，先追加明确范围再执行 |

本计划需要批准的核心决策：**共享无状态协议 + 保留旧认证适配；显式账户身份；工厂独占所有权；按账户弱注册RLock；新登录保守接受门槛与失败清状态；FAILED显式恢复；新订单禁重定向；旧新混用并发边界。** 这些决定全部写在本文，不留给Build自行猜测。

## 18. 原 Plan 起草阶段的交付事实（历史记录）

- 已完成源码/测试/需求/历史证据的只读核对及Git身份检查。
- 本次唯一写入是允许计划目录中的本文；仓库生产、测试、配置和需求文件均未修改。
- 未运行任何测试/CI/真实请求，未提交或推送；所有待实施检查均明确标为未来步骤。
- 下一步：人工审阅并批准设计；需要归档或实施时切换Build agent。P2完成仍需实际测试、Linux禁网证据、远端CI和独立Review。

## 19. 本次仓库归档记录

- 授权范围：维护者明确要求输出完整 P2 计划并保存至 `docs/refactor/plans/P2-plan.md`；不得修改生产代码、执行真实交易、自动提交或推送。
- 已归档全部设计正文、Kill Test、状态所有权与转换表、架构比较、逐函数兼容表、P1 接缝映射、文件范围、分批步骤、测试命令、验收、回滚与风险。只更新文档归档状态，未批准或实施设计。
- 归档前再次核对：HEAD 仍为 `e35cf1782c4dded98fc4ce2ad3dce4c56648e28a`，分支仍为 `refactor/p2-client-isolation`；工作区只有原先未跟踪的 `docs/refactor/requirements/P2.md`。第 1 节是起草时基线，不把新归档文件倒填为当时已存在。
- 本次仅新增本文；原起草副本、生产代码、测试、配置、需求和历史报告保持不变。
- 归档验证限定为文档完整性、Markdown 结构、空白检查和 Git 修改范围核对；未运行 pytest、tox、Docker、CI 或任何交易请求。
- 后续仍需人工批准核心设计与实施范围，并满足第 17 节审批/阻断条件后才可开始 S0；不得因文件已经归档而自动进入 Build。

## 20. 实施批准与 S0 基线（2026-11-07）

- 维护者在本次会话明确批准本文设计并授权实施，随后明确确认“P1 已有最终 Review PASS”。后者为维护者提供的信息，未提供审查记录路径，本次不冒称独立核验或补签 P1 Review。第 0、17、19 节此前的待批准描述保留为归档时的历史记录，本节记录后续批准。
- 实施基线仍为 `e35cf1782c4dded98fc4ce2ad3dce4c56648e28a`；分支 `refactor/p2-client-isolation`；开始时只有 P2 需求与计划两个未跟踪文件。没有 fetch，不假称在线核验了远端最新状态。
- S0 实测：Python 3.11.14、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2、tox 4.67.12、requests 2.31.0。
- OS 探针：`sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))'` 退出 1，明确 `PermissionError: Operation not permitted`，符合预期阻断；未访问外网。
- 原始基线：`PYTHONDONTWRITEBYTECODE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -m pytest -p no:cacheprovider -q` 退出 0，168 passed in 7.28s。
- 后续结果与计划偏差记录于 `docs/refactor/reports/P2-acceptance.md`。不自动提交、推送或发布；不执行真实交易。

## 21. S6 Linux 最终快照验证补充

- 原 `ci/offline.Dockerfile` 已实际构建成功；构建期间新增的 headers 所有权收口造成该镜像3个Python文件与最终工作区不同，不将其直接当最终受测快照。
- 依赖、打包元数据、tox、CI及Dockerfile没有变化。最终验证复用原Dockerfile成功准备的Python3.11/tox依赖镜像，用标准输入传入的薄Docker构建描述，仅COPY最终 `src/`、`tests/`、`docs/`；不重新安装依赖或修改已提交Dockerfile。
- 薄层构建和执行均 `--network none`；先验证其基础镜像层与原准备镜像一致，再比对全部34个生产/测试/CI Python文件SHA256（排除生成_version/缓存），最后执行既有 `ci/run_offline_tests.py` 完整三入口及导出原始报告。
- 必须保存原构建结果、薄层构建的完整stdin/参数/退出码、两个镜像ID、源码比较、NetworkMode、容器退出码及全部报告；工作区/镜像若不一致即停止验收。此调整只改变本地验证准备效率，不变更生产接口/请求行为，也不替代最终远端CI及独立Review。

## 22. 本地阶段验证完成记录

- S0–S6已完成本地实施与验证；最终macOS系统禁网tox342项通过。最终Linux镜像与工作区34个Python文件哈希一致，`--network none` 下默认tox、仓库外不同顺序、显式tests三轮各342项通过，旧168个节点全部保留。
- 最终Linux镜像为 `sha256:18917d38237a8c8511de77052e272723450fcf7a94a2e6eb85cdf6707c4631e4`；完整参数、失败/重跑、网络证据、实际版本和原始报告导出路径见 `docs/refactor/reports/P2-acceptance.md` 第6节。
- S7远端CI及独立Review尚未执行，P2总体验收为NEEDS EVIDENCE；不自行代签PASS。没有commit、push、tag或发布，没有真实请求。
