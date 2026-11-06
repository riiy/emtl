# emtl P0 安全基线实施计划

> Review 后用户批准的调整及执行结果见第 16 节及以后；其中 CLI 输出与测试入口调整覆盖前文历史设计。P0 范围及交易 API 兼容性约束不变。

## 1. 文档状态与执行边界

- 阶段：仅 P0；依据 `AGENTS.md`、`docs/refactor/requirements/P0.md`。
- 分析日期：2026-11-06。
- 仓库：`/Users/lld/emtl`；分析时分支：`refactor/p0-security`。
- 分析基线：`89328a75ea42362587fb46e6a9f395d0ca90ee86`，提交标题 `Bump version: 0.2.5 → 0.2.6`。
- 目标归档路径：`docs/refactor/plans/P0-plan.md`。
- 初始工作区：`git status --short --branch` 显示 `docs/refactor/` 未跟踪；其中已存在本阶段需求文件。不得覆盖、清理或当作本次新增内容删除。
- 本文是实施方案，不是完成报告。已完成源码阅读、配置检查及标准库 AST 签名核对；未执行 pytest、tox、CLI、OCR 初始化、网络请求或真实交易。

### P0 交付目标

1. 形成可审查的现有公共 API 契约文档及离线契约测试。
2. 清除 emtl 自身日志中的凭证、认证令牌、验证码、交易请求及完整敏感响应。
3. 消除库导入和 `get_logger()` 对宿主 root logger 的全局配置副作用。
4. 将全部自动测试改为离线执行，阻断意外网络访问；删除 CI 的交易账户凭证注入。
5. 保留现有 Python 登录、查询、下单、撤单的调用方式、请求语义及成功返回结构。

### 不在本阶段实施的工作

TradingClient、多账户隔离、并发锁、会话生命周期重构、OCR 生产初始化重构、统一异常体系、重试策略、请求超时改造、返回模型封装、Python 最低版本/依赖迁移。现有全局 session、OCR、认证状态是后续阶段问题。

不得为真实下单新增 dry-run 默认值、确认参数、环境开关、参数校验或自动重试。测试隔离必须位于测试基础设施，而非改变生产交易接口。

## 2. 已核实的代码事实

以下行号以分析基线为准，实施后可能移动。

| 文件 | 核实结果 | P0 意义 |
| --- | --- | --- |
| `src/emtl/core.py:18-21` | 导入时创建 logger、`DdddOcr(show_ad=False)`、全局 `Session()` 和空认证令牌 | 契约测试须先建立测试环境，再导入包；不能假定直接导入无初始化成本 |
| `src/emtl/core.py:41-44` | 非 200 响应日志输出 URL、状态码、完整 body，随后裸 `raise` | URL 可带令牌；修改日志时不能顺手改异常行为 |
| `src/emtl/core.py:47-71` | 无令牌则 `login()`；INFO 输出令牌；DEBUG 输出请求数据和含令牌 URL | 主泄漏路径；保持自动登录、URL 拼接、POST 结构 |
| `src/emtl/core.py:74-88` | 验证码用导入别名 `requests.get`，不走全局 session；失败日志包含 OCR 结果和异常文本；非整数结果递归重试 | 只 mock 全局 session 无法隔离网络；不改变既有验证码重试逻辑 |
| `src/emtl/core.py:104-139` | 空用户名/密码分别回退到环境变量；POST 后调用 `resp.json()` 写日志，再提取令牌；只捕获 `KeyError` | JSON 求值本身影响控制流，不能只删除整句日志而跳过原解析 |
| `src/emtl/core.py:202-233` | 下单成功路径先解析 JSON 写日志，再解析 JSON 返回；撤单返回去首尾空白后的文本 | 不可将撤单改成 JSON；不引入下单重试 |
| `src/emtl/utils.py:19-24` | 每次 `get_logger()` 都调用 `logging.basicConfig(..., force=True, level=INFO)` | 导入包可替换并关闭宿主 root handlers |
| `src/emtl/cli.py:18-23` | 记录原始 args、解析后的 Namespace，并向 stdout 打印用户名和密码 | 日志和 stdout 是两个独立泄漏点；stdout 有已断言的兼容性契约 |
| `src/emtl/tests/test_core.py` | 10 个测试全部未 mock、未 skip；包含真实登录、账户查询、行情、下单、撤单 | 不能直接运行现有测试建立动态基线 |
| `src/emtl/tests/test_cli.py:5` | 真实启动 `emt` 子进程，断言 `foo bar\n` | 子进程不会继承 pytest 的 Python monkeypatch；stdout 不能未经批准改动 |
| `.github/workflows/github-actions.yml` | matrix test、finish test、codecov step 三处注入 `EM_USERNAME/EM_PASSWORD`，共六条变量配置 | 三处都必须移除 |
| `tox.ini:8-9,28-29` | bootstrap 和通用 testenv 使用 `passenv = *` | 本机账户环境变量也可能进入测试环境 |
| `pytest.ini` | `--pyargs emtl`、doctest 模块收集、RST doctest、warnings-as-errors | 网络阻断需覆盖收集期，不能仅依赖测试函数级 fixture |
| `setup.py:72-85` | 声明 Python `>=3.10`；console script 为 `emt = emtl.cli:run` | 保留入口；版本迁移不并入 P0 |
| `src/emtl/__main__.py` | `python -m emtl` 调用同一 `run()` | 需要 CLI 入口回归 |

### 已检查的其他配置

- `.github/workflows/document.yml`：未发现交易账户凭证；有 GitHub 文档发布 token。
- `.github/workflows/release.yml`：未发现交易账户凭证；使用 PyPI trusted publishing，Python 3.10。版本不一致记录为后续工作。
- `docs/usage.rst`：展示登录、资产查询、下单和撤单；是普通 `code-block`，当前不是可执行 doctest。示例下单/撤单名称未带 `emtl.` 前缀，修正文档时保持既有调用形式并使用明显虚构占位值。
- `docs/reference/emtl.rst`：目前仅自动生成 API，没有明确的签名、返回、兼容性契约。
- `docs/conf.py`：Sphinx 只配置 `.rst`；Markdown 契约文档应从现有 RST 参考页提供下载/源码入口，无需引入 Markdown 扩展。
- `tox -e docs` 包含 `sphinx-build -b linkcheck`，会访问外部链接；不得把它当作离线自动测试验收命令。
- `.pre-commit-config.yaml`：ruff 配置含 `--fix`，black 也会改文件；Plan 阶段不运行这些检查。

## 3. 现有公共 API 契约清单

### 3.1 包级导出

`src/emtl/__init__.py` 的 `__all__` 顺序为：

```python
[
    "login",
    "query_asset_and_position",
    "query_orders",
    "query_history_orders",
    "query_trades",
    "query_history_trades",
    "query_funds_flow",
    "create_order",
    "cancel_order",
]
```

以上名称均直接引用 `emtl.core` 的同名函数。保留名称、导入路径、参数顺序、默认值、参数种类及现有注解；不添加 wrapper 或新导出。`emtl.__version__` 当前为 `0.2.6`，P0 不进行版本发布或修改该值。

| 现有签名 | 当前返回/行为 | 离线契约要点 |
| --- | --- | --- |
| `login(username: str = "", password: str = "", duration: int = 30) -> Optional[str]` | 成功提取 HTML 隐藏字段后返回 strip 后的令牌并写全局状态；无匹配返回 `None`；try 内 `KeyError` 被捕获后返回 `None` | 显式参数、分别回退环境变量、strip、duration 原样传递、加密密码、验证码、POST 后 GET 提取令牌 |
| `query_asset_and_position()` | response 为真时原样返回 `resp.json()`；否则 `None` | tag=`query_asset_and_pos` |
| `query_orders()` | 同上 | tag=`query_orders` |
| `query_trades()` | 同上 | tag=`query_trades` |
| `query_history_orders(size, start_time, end_time)` | 同上 | tag=`query_his_orders`，数据 `qqhs/dwc/st/et` |
| `query_history_trades(size, start_time, end_time)` | 同上 | tag=`query_his_trades`，数据 `qqhs/dwc/st/et` |
| `query_funds_flow(size, start_time, end_time)` | 同上 | tag=`query_funds_flow`，数据 `qqhs/dwc/st/et` |
| `create_order(stock_code, trade_type, market: str, price: float, amount: int)` | response 为真时返回第二次 `resp.json()` 的结果；否则 `None` | tag=`create_order`；不封装、不解释业务 Status；一次订单 POST |
| `cancel_order(order_str: str)` | response 为真时返回 `resp.text.strip()`，类型为 `str`；否则 `None` | tag=`cancel_order`，请求 `revokes=order_str.strip()` |

**返回类型说明：** 查询/下单代码没有验证 JSON 类型或完整券商 schema。契约应描述为“原样透传 JSON 解析结果，典型为 dict”，不得声称已验证所有真实响应字段；测试中的嵌套 JSON、`Status/Data` 等只是合成样本，不代表完整券商协议。

### 3.2 子模块直接可用的函数

这些名称虽不在包级 `__all__`，仍是已有调用面，保持可导入与现有签名：

| 路径/签名 | 行为 |
| --- | --- |
| `emtl.core.get_last_price(symbol_code: str, market: str) -> float` | 行情 JSON 为 `None`、缺少小写 `status` 或 `status != 0` 时返回 NaN；否则对 `realtimequote.currentPrice` 调用 `get_float()` |
| `emtl.utils.get_logger(name)` | 返回同名 `logging.Logger`；P0 明确批准的目标是移除 root 配置副作用 |
| `emtl.utils.emt_trade_encrypt(content: str) -> str` | UTF-8 文本用现有公钥、PKCS1v15 加密，返回 base64 字符串；公钥不是秘密，不删除或替换 |
| `emtl.utils.double_equal(a, b) -> bool` | `abs(a-b) < 1e-6` |
| `emtl.utils.get_float(data: dict, key: str) -> float` | 对字段值 strip，非空转 float，否则 `0.0`；缺失键仍可能抛 `KeyError` |
| `emtl.utils.get_int(data: dict, key: str) -> int` | 同上，非空转 int，否则 `0` |
| `emtl.cli.run(args=None)` | argparse 解析后退出；现有 CLI 契约见下节 |

不为本次完全未修改的数值转换/加密实现新增大量镜像单测；记录签名即可。登录测试通过假的加密函数确认传参与调用，不依赖真实账户密码。

### 3.3 请求与错误行为边界

- `_query_something()`：无全局令牌时调用 `login()`；已有令牌时不登录；默认表单是 `{"qqhs": 100, "dwc": ""}`；URL 为 `_urls[tag] + validate_key`；添加 `X-Requested-With: XMLHttpRequest`。
- 历史查询表单是 `{"qqhs": size, "dwc": "", "st": start_time, "et": end_time}`。
- 下单表单严格保留 `stockCode/tradeType/zqmc/market/price/amount`，`zqmc` 为空字符串；不额外 strip/转换订单参数，不改变 B/S 的传递方式。
- 撤单表单严格保留 `revokes`；行情 GET 保留 `id=symbol_code.strip()` 和原 market。
- 保留 `_urls`、基础 headers、请求方式、现有 timeout 有无及 session/cookie 使用方式。验证码 GET 的 `timeout=60` 不变。
- 当前非 200 路径使用裸 `raise`，在没有活动异常的普通调用下会产生 `RuntimeError: No active exception to reraise`。这不是理想设计，但 P0 只改日志，不改为 `raise_for_status()` 或新异常。
- 不新增业务 `Status` 判断，不将网络异常转换为 `None`，不对下单异常自动重试。
- `login()` 不能因移除日志而省略原本的 `resp.json()` 求值，尤其是畸形 JSON 抛异常的行为。
- `create_order()` 此阶段保留原先两次 JSON 求值的顺序及返回路径；暂不合并解析，避免在安全改动中夹带控制流变化。

### 3.4 CLI 契约与待决事项 B1

现有入口：`emt`、`python -m emtl`、`emtl.cli.run(args=None)`。

参数：`-u/--user`、`-p/--password`；buy/sell/query 互斥；query choices 为 `asset/order/trade`。当前 CLI 只解析并打印输入，没有实际执行交易，不得在 P0 实现交易命令。

- 清除 `logger.info(args)` 两处敏感日志属于 P0 授权范围。
- 当前 `print(args.user, args.password)` 会泄漏凭证，但现有测试明确断言该 stdout；`AGENTS.md` 要求 CLI 可观察变更事先批准。
- **B1：需人类明确决定 CLI stdout 兼容性例外。** 推荐批准“取消凭证回显”，保留入口、参数和正常退出码，不新增其他提示输出，并更新 CLI 测试和变更记录。
- 未批准前，不修改这一 stdout 契约，不把“清理日志”描述为“所有输出均无敏感数据”。可以推进其他步骤，但完整安全收口验收保持阻断。
- 如果负责人明确要求保留 stdout，必须记录接受该已知风险及“无敏感日志不等于无敏感 stdout”的验收边界；不得静默豁免或把未批准建议当作已批准变更。

## 4. 敏感信息传播与整改策略

| 来源 → 传播路径 | 现有输出位置 | 处理方案 |
| --- | --- | --- |
| 参数/`EM_USERNAME` → strip → 登录 `userId` | CLI args/Namespace 日志及 stdout；响应可能回显 | 删除 args 日志；stdout 按 B1；生产登录参数和环境回退不变 |
| 参数/`EM_PASSWORD` → strip → RSA/base64 → 登录表单 | CLI 明文日志/stdout；后续异常或响应可能包含派生值 | 不记录明文、密文、表单；合成哨兵覆盖明文和密文 |
| OCR content → `identifyCode`；OCR 转换异常 | `core.py:85` 的 code 与异常文本 | 使用固定事件文本，不记录 code、captcha image 或异常字符串 |
| 登录 JSON/HTML → `_em_validate_key` → 查询 URL | `core.py:58,68`，以及非 200 的 URL/body | 删除令牌日志；禁止完整 URL/查询串进入日志 |
| session cookies → 后续 HTTP headers | 当前未发现直接 cookie 日志；完整响应/异常存在间接传播可能 | 不新增 session、headers、request/response 对象输出；合成 cookie 哨兵回归 |
| 查询数据、订单参数、撤单编号 → 表单 | `core.py:68` 的 req_data | 删除原始请求数据，最多保留受限的内部操作 tag |
| 登录响应、订单响应及任意错误 body | `core.py:43,136,221` | 仅固定事件文本、必要的数字 HTTP 状态码；不输出 JSON/body/Message |
| `KeyError` 文本和 response 对象 | `core.py:139` | 固定失败事件，保持原 catch/return 行为；不使用 `exc_info=True` |

### 日志实现约束

1. 优先删除数据型日志；需要诊断时用固定事件名称，如“authentication response received”“order response received”。HTTP 200 不代表业务成功，避免无依据的 success 文案。
2. 允许字段仅为已验证的内部 tag、数字 HTTP status；未知/外部提供的 tag 不直接写日志。不引入通用“打印一切再正则脱敏”机制。
3. 不把敏感对象传入 logging，即使它们在 INFO 等级下通常不会格式化。回归检查不仅看最终文本，也看 `LogRecord.msg/args` 和异常信息。
4. `_check_resp()` 不读取 URL/body 来生成日志，保留原异常语义；OCR、login 的失败日志不拼接异常文本。
5. `get_logger(name)` 简化为返回 `logging.getLogger(name)`，不调用 `basicConfig`，不设 root 或第三方 logger 的 level/handlers，不关闭 handler，不重复添加 handler；保持正常传播，由宿主选择格式与等级。
6. 不以提高日志等级、关闭 propagation 或全局禁用 logging 掩盖泄漏；DEBUG 下也必须通过测试。
7. 保留日志表达式原本影响控制流的必要求值，尤其 login/create_order 的 JSON 解析。

**边界：** 本阶段保证 emtl 主动生成的日志符合以上规则；用户自行打印返回值、显式启用外部 HTTP wire trace 或将异常完整写出，不受库日志实现完全控制。不得为限制这些行为改变返回数据或全局劫持第三方 logger。

## 5. 自动测试与真实交易隔离设计

### 5.1 现有测试去向

`test_core.py` 的十个测试全部重写为假的 HTTP/OCR/环境下的契约测试，覆盖原有功能意图。真实券商调用不再保留为任何 `test_*.py`、可被 marker 打开的 live suite 或 CI 步骤。

真实登录、下单和撤单的调用形式保留在人工使用文档中，使用明显虚构占位值；不创建可被发现执行的实盘脚本，也不执行人工实盘验证作为 P0 前提。

`test_cli.py` 保留 CLI 行为验证，但子进程需独立安装离线阻断和假 OCR。仅把凭证改成空值、设置 skip marker 或在 pytest fixture 中 mock session，都不算隔离完成。

### 5.2 收集前的离线保护

采用只存在于测试中的轻量辅助模块，不给生产接口增加依赖注入参数：

1. 新增 `src/emtl/tests/_offline.py`，本身不导入 emtl；提供可逆的测试进程网络阻断与假 OCR 安装逻辑。根 `conftest.py` 在 emtl 收集/导入前加载它；可按文件路径用 `runpy` 加载，避免为了导入辅助模块先触发 `emtl.__init__`。
2. 根 `conftest.py` 在初始加载阶段清除继承的 `EM_USERNAME/EM_PASSWORD`，不要打印原值；在首次 emtl 导入前完成保护，清理在 pytest 结束时恢复。
3. 默认拒绝真实 requests 传输（至少 `Session.request/send` 的出网兜底）以及 socket 建连/DNS 路径；按实际实现涵盖 `create_connection`、`connect/connect_ex`、地址解析，不能只 mock `session.post`。
4. 阻断异常只返回固定文本，不包含 URL、请求体、headers 或被拦截的参数。保护必须在 collection 阶段已生效，autouse fixture 仅负责每个测试的状态重置。
5. 在导入 emtl 前替换 `ddddocr` 为测试专用最小模块，构造假 DdddOcr；未明确安排的识别调用直接失败。无需运行模型、下载模型或改生产代码。
6. 每例替换 `core.session`、`core.ocr`、`core.get` 并复位 `_em_validate_key`；未安排的 HTTP/OCR 调用以固定错误失败，防止测试依赖顺序。
7. 成功路径用真实 requests Response 的合成内容或忠实 fake，正确模拟 bool、status_code、json、text。不要因 mock 默认 truthiness 改写实际语义。

网络 guard 的负向自检也必须自身离线：在被测拦截层下设置会立即失败的底层哨兵/传输替身，或使用等价的隔离启动器，验证上层 guard 优先拒绝且底层未被调用。不得用真实券商 URL、可路由地址或真实 DNS 请求来证明“网络应该被挡住”；即使被测 guard 有缺陷，自检也不能出网。

支持并验收从仓库根目录运行的默认 pytest、显式测试目录、`pytest --pyargs emtl` 和 tox py311-cover。若实际 pytest 加载顺序导致任何受支持入口先导入 emtl 再执行根 conftest，停止该入口验证，先将相同 bootstrap 前移为显式 pytest plugin；不得降低为函数级阻断后继续运行。此项通过收集期回归证实，不凭假设放行。

### 5.3 子进程

- 不再无保护执行 `subprocess.check_output(["emt", ...])`。
- 为 CLI/导入隔离测试启动 `sys.executable`，在子进程内先按文件路径载入离线 helper、安装网络阻断及假 OCR，再执行入口。
- `python -m emtl` 可用受保护的 `runpy.run_module("emtl", run_name="__main__")` 验证模块入口；已安装 `emt` 脚本可在同样 bootstrap 下以 `runpy.run_path()` 执行，设置正确 argv，同时检查 distribution entry point 仍为 `emtl.cli:run`。
- 明确说明测试使用保护启动器，不声称直接运行未保护的原始命令。必要时对入口安装缺失报前置条件错误，不伪造为通过。
- 子进程 env 显式去除真实账户变量，只传所需基础变量；参数仅使用固定假数据。

## 6. CI 和 tox 方案

1. 删除 `.github/workflows/github-actions.yml` 三处 `EM_USERNAME` 与 `EM_PASSWORD` 注入，包括 codecov step，共六条。
2. 保留 CODECOV_TOKEN、GITHUB_TOKEN 和 PyPI trusted publishing 配置；它们不是交易账户凭证。
3. 将 `tox.ini` bootstrap 与通用 testenv 的 `passenv = *` 改为执行需要的显式白名单；初始只保留实际使用的 `TOXPYTHON`、`PYTEST_ADDOPTS`，必要的操作系统基础变量遵循 tox 默认规则。若代理/证书配置确实必需，再逐项列明，不能恢复 `*` 或 `EM_*`。
4. 通用测试环境显式将 `EM_USERNAME/EM_PASSWORD` 设为空值作为兜底；测试环境回退行为时，由 monkeypatch 写入假值。
5. py311-cover 继续执行离线测试；测试执行不依赖 GitHub Secrets。CI 安装依赖、Actions 自身及覆盖率上传仍可能需要网络，这与测试代码禁止网络分开记录。
6. 增加静态安全回归：遍历现有全部 workflow，拒绝交易凭证注入；解析 tox 配置，拒绝通配 passenv 或账户变量穿透。不为此引入新 YAML 运行时依赖，可检查受限结构/文本并辅以 Review 全文件检查。
7. 检查矩阵和 finish 的两次测试都使用同一安全配置；P0 不顺手重构重复 CI 流程。

## 7. 文件修改范围

### 必须修改或新增

| 路径 | 动作与范围 |
| --- | --- |
| `src/emtl/core.py` | 修改全部已列出的敏感日志及必要等价求值；不改请求、签名、返回路径、重试 |
| `src/emtl/utils.py` | 仅修复 `get_logger()` 的全局配置副作用 |
| `src/emtl/cli.py` | 删除原始/解析参数日志；stdout 只在 B1 批准后变更 |
| `conftest.py` | 新增收集前离线 bootstrap，范围覆盖默认 pytest 和 doctest 收集 |
| `src/emtl/tests/_offline.py` | 新增测试专用离线/假 OCR 支持，供父进程与子进程复用；不得成为生产运行分支 |
| `src/emtl/tests/conftest.py` | 新增测试级 fake、账户环境和全局状态复位 fixtures |
| `src/emtl/tests/test_core.py` | 将十个 live 测试改为离线请求/返回契约测试并补关键分支 |
| `src/emtl/tests/test_cli.py` | 改成受保护启动，验证参数、入口、退出码、日志；stdout 依据 B1 |
| `src/emtl/tests/test_api_contract.py` | 新增 exports、签名、函数绑定、返回透传及兼容性断言 |
| `src/emtl/tests/test_logging_safety.py` | 新增 DEBUG 哨兵泄漏测试、JSON 控制流、root logger 隔离测试 |
| `src/emtl/tests/test_test_safety.py` | 新增收集期/运行期/子进程断网和 CI/tox 静态安全回归 |
| `.github/workflows/github-actions.yml` | 移除三处交易账户注入 |
| `tox.ini` | 缩小环境变量传递范围、清空测试账户变量；仅必要的安全执行配置 |
| `docs/refactor/contracts/P0-public-api.md` | 新增独立契约文档，包含本文第 3 节及最终 B1 决定 |
| `docs/refactor/plans/P0-plan.md` | Build 获准后归档本计划及明确批准的决定 |
| `docs/reference/emtl.rst` | 给出契约 Markdown 文件的可访问下载/源码链接 |
| `docs/usage.rst` | 使用明确虚构占位值、正确 `emtl.` 调用前缀，说明自动测试已离线及人工示例边界 |
| `CONTRIBUTING.rst` | 更新离线测试入口、前置依赖准备、禁止测试用真实账户；当前工作流以 AGENTS 为准，不自动 push |
| `CHANGELOG.rst` | 记录日志行为调整、测试/CI 隔离，以及获批 CLI 输出变化 |

### 有条件修改

- `pytest.ini`：只有收集前保护/测试发现确需调整时修改最小相关设置；保持已支持的默认和 `--pyargs emtl` 测试入口，解释每处变更。
- 若必须使用显式 pytest plugin 前移 bootstrap，可调整 `_offline.py` 的放置/加载路径及 tox 的测试专用 PYTHONPATH；先更新计划的文件清单并审查，不能改生产模块来迁就测试。

### 检查但预期不修改

`src/emtl/__init__.py`、`src/emtl/const.py`、`src/emtl/__main__.py`、`src/emtl/_version.py`、`setup.py`、`pyproject.toml`、`uv.lock`、`ci/requirements.txt`、其他两个 workflow 和 `docs/conf.py`。如出现这些文件的 diff，逐项解释并确认不是打包/安装工具产生的无关改动。

## 8. 可验证的小步骤与依赖

### S0 — 固定基线、批准范围

1. 重新读取 AGENTS、P0 需求及本计划；确认只批准 P0，且已切换到可执行 Build 的模式。
2. 记录 HEAD、分支、tracked/staged/untracked 清单。保护已有 `docs/refactor/requirements/P0.md`。
3. 对照本文核实源码未发生影响计划的变化；若已变化，更新基线再执行。
4. 记录 B1 决定；未决定时只推进不涉及 stdout 的工作。
5. 确认 Python 3.11、运行依赖、pytest/pytest-cov 和所需 lint 工具已在可用环境中；依赖准备与离线验收分开。

**通过条件：** 基线和文件归属明确，未运行旧 live 测试，未读取/打印任何真实账户变量。

### S1 — 落地契约文档与测试安全底座

1. 建立第 3 节的契约文档；标明源码事实和合成样本，不虚构券商字段。
2. 先实现收集前网络阻断、假 OCR、环境隔离及测试级状态重置。
3. 用专门的无网络自检验证 guard 在调用底层网络前抛固定异常；包括 requests、验证码别名和 socket 路径。
4. 检验导入及 doctest collection 均在 guard 保护内；子进程单独 bootstrap。

**通过条件：** guard 自检通过；未经安排的网络调用失败；收集过程不启动真实 OCR 或发送请求。

**顺序约束：** 此时不得执行仍包含 live 测试的完整 suite。S1/S2/S3 在全部完成前，不形成可运行旧 live 测试的 CI 提交。

### S2 — 替换 live 测试、锁定原有契约

1. 重写全部十个 core 测试，mock 网络和 OCR，不使用真实环境变量或时间依赖样本。
2. 增加包级导出/签名与请求/返回契约断言；先针对未改日志的生产代码运行契约子集。
3. CLI 改用受保护启动器；先锁定现有参数、退出码、入口和当前 stdout。
4. 覆盖登录空值回退、已有令牌不重复登录、响应 JSON 透传、撤单文本 strip、行情 NaN、异常不重试。

**通过条件：** 契约子集在未做生产日志改动前离线通过，形成可比较基线；任何测试失败都不得退回真实网络验证。

### S3 — 移除 CI 凭证并收紧 tox

1. 删除六条交易凭证注入。
2. 替换两处 `passenv = *`；设置空账户值。
3. 增加配置回归，并用合成父进程账户变量验证 tox 中不会继承该值。

**通过条件：** 全 workflow 无交易凭证注入；tox 不能穿透父进程账户值；CI 测试可在没有账户 Secrets 时执行。

S1+S2+S3 建议形成第一个原子提交边界；提交前必须运行离线测试，避免中间提交恢复真实交易执行机会。

### S4 — 清理 core/CLI 日志，保持控制流

1. 删除令牌、原始请求、URL/body/JSON、OCR 和异常文本日志，采用固定事件/允许字段。
2. 将 login/create_order 原日志中的必要 JSON 求值保留下来，保持调用顺序和异常路径。
3. 为每条被修改日志先建立 DEBUG 哨兵回归，验证在旧实现会失败、新实现通过。
4. 清理 CLI args 日志；B1 已批准时取消凭证 stdout 并更新专门的契约例外测试。

**通过条件：** 日志哨兵全部通过，S2 契约测试继续通过；仅 B1 明确批准的 stdout 断言允许改变。

### S5 — 修复 logging 全局副作用

1. `get_logger()` 只返回命名 logger。
2. 在新鲜、受保护子进程中预置 root handler/formatter/level，导入 emtl、emtl.cli 并重复调用 get_logger。
3. 比较 root 配置、handler 对象、formatter、level、filters、handler 是否被关闭及全局 logging 禁用状态；验证宿主 handler 仍能收到安全日志且没有重复输出。
4. 再测无宿主配置场景，确认不会自动配置 root。

**通过条件：** 配置前后保持一致；logger 名称/身份正确；不会因日志等级改变导致 JSON 控制流变化。

### S6 — 完整离线验收、Review 与归档

1. 按第 9 节执行适用命令，记录退出码、测试数量及限制。
2. 更新契约、使用说明、贡献说明、changelog 和计划决策记录。
3. 同时审查 tracked、staged 和 untracked 文件；逐项对照第 7 节。
4. 对照第 10 节验收；任何阻断未解除，报告“P0 未完成”，而非用通过的子集代替完整结论。
5. 仅在离线检查完成后提交；不自动 push、publish、tag。

## 9. 测试矩阵与执行方式

### 9.1 必须覆盖的测试

| 分类 | 用例 | 成功标准 |
| --- | --- | --- |
| API | 九项导出、顺序、core 同名绑定、签名、默认值、子模块接口 | 无意外新增/删除、改参或 wrapper |
| 登录 | 显式凭证、分别回退假环境值、strip、duration、验证码表单、提取令牌、无令牌匹配 | 请求和全局状态与基线一致；调用次数受控 |
| 通用请求 | 有/无令牌；默认/显式表单；headers、URL | 只使用 fake HTTP，认证顺序不变 |
| 查询/下单 | 六个查询 API、下单表单、嵌套 JSON/未知字段/非零业务 Status | 透传响应、不丢字段、不强制成功、不新增订单重试 |
| 撤单 | 入参和响应两端空白 | 表单值正确；返回 str，不转 JSON |
| 行情 | 合成正常价格、空价格、缺 status、非零 status、None | 对应 float/0.0/NaN；不连接行情服务器 |
| 错误兼容 | 非 200、畸形 JSON、login try 内 KeyError、请求异常、OCR 一次非法后合法 | 保留原异常/None/递归行为；用有限 stub 防止无限递归；订单请求不重试 |
| 日志泄漏 | 正常登录、查询、下单、撤单、HTTP 错误、OCR 错误、login KeyError、CLI 参数 | DEBUG 捕获中无任何敏感哨兵，Record msg/args/异常信息不承载敏感对象 |
| 日志宿主 | 有/无 root 配置、导入、重复 get_logger、宿主接收日志 | handler/level/formatter 不变，无关闭和重复 handler |
| 测试安全 | collection、普通测试、验证码 GET、session POST/GET、socket、子进程 | 未 mock 的网络在出网前失败；错误文本不带输入 |
| 环境隔离 | 父进程存在合成账户值、无账户值、单例独立执行 | 账户值不继承、不串测试；成功与否不依赖真实账户 |
| CI/tox | 所有 workflow 和有效 tox 环境配置 | 无交易凭证注入，无 `passenv=*`/`EM_*` 穿透 |
| CLI | entry point、模块入口、help、互斥项、query choices、正常/错误退出码 | 与基线一致；stdout 只按 B1 的明确例外改变 |

敏感哨兵使用唯一且明显虚构的 `P0_FAKE_*` 值，分别覆盖用户名、明文密码、加密串、令牌、验证码、Cookie/Authorization 字段、订单号、订单参数和嵌套响应。将它们放入 URL query、body、JSON 和异常文本，证明各出口均被处理。不要用真实响应录制或生产账号长度样例冒充合成凭证。

### 9.2 Build 阶段执行命令

前置条件：仓库根目录；Python 3.11 环境已安装项目和测试依赖；所有 live 测试已被替换；收集前 guard 自检已通过。以下命令本次 Plan 均未执行。

```bash
# 先验证测试基础设施；此命令也必须经过收集前 guard。
python -m pytest src/emtl/tests/test_test_safety.py -q

# 契约和核心行为。
python -m pytest src/emtl/tests/test_api_contract.py src/emtl/tests/test_core.py -q

# 日志、宿主配置和 CLI。
python -m pytest src/emtl/tests/test_logging_safety.py src/emtl/tests/test_cli.py -q

# 默认入口；显式 package 入口应至少验证一次。
python -m pytest -q
python -m pytest --pyargs emtl -q

# 与 CI 相同的覆盖率环境，依赖预先可用后执行。
tox -e py311-cover -v

# 无自动修复的静态检查。
ruff check src/emtl conftest.py
black --check src/emtl conftest.py
git diff --check
```

- guard 是每次自动测试执行的强制条件，不能为了让命令通过临时关闭它。
- tox 新建环境/构建包可能尝试下载安装依赖；离线验收时应使用已准备好的环境或完整本地 wheel/cache，并关闭索引访问，例如设置 `PIP_NO_INDEX=1`。环境缺依赖导致失败时标记“环境阻断”，不能将联网补装与离线测试混为一谈。
- 可在依赖已缓存时执行 `tox -e check`；其 pre-commit hooks 会自动修复文件，执行后重新检查 diff，并对实际新改动重跑相关测试。
- 文档构建若需要，使用已准备环境中的本地 HTML 构建并确保不会访问网络；不要运行 linkcheck 作为离线验收。Markdown 契约通过 RST download/source 链接人工验证可发现。
- 无须真实登录、验证码服务、下单、撤单或行情请求验证本计划。也不声称离线测试证明了券商线上当前可用性。
- 对各测试文件独立运行或选取认证/下单/日志测试单独运行，验证无顺序依赖；不为重复取得同一结果无条件反复跑全套。

## 10. 验收门禁

- [ ] 公共 API 契约文档已形成并可从参考文档发现；签名、导出、成功返回结构与基线一致。
- [ ] 下单/撤单请求结构、登录环境回退、自动登录、URL/headers/调用次数及异常传播没有未经批准的变化。
- [ ] 全部已识别敏感日志路径均有测试；DEBUG、LogRecord、异常分支未泄漏哨兵。
- [ ] 库导入和 `get_logger()` 不改 root 配置或关闭宿主 handlers；安全日志仍可由宿主捕获。
- [ ] 原十个 core 测试全部离线，CLI/导入子进程也受保护；默认收集、doctest、显式 `--pyargs emtl` 和 tox 入口不会访问券商。
- [ ] 自动测试无需账户环境变量，CI 三处注入已移除，tox 环境不能透传真实账户。
- [ ] 无新增自动订单重试、live marker 入口或可被收集执行的交易示例。
- [ ] B1 已有明确决定：批准取消凭证回显并通过例外测试，或由负责人明确接受保留 stdout 的已知风险和验收边界。无决定即阻断完整收口。
- [ ] 适用离线测试和检查实际运行通过；未运行或环境阻断的项目单独列出，没有“估计通过”。
- [ ] Review 已审查 tracked、staged、untracked 内容；无无关文件、真实数据或意外生成版本变更。
- [ ] 没有 push、publish、tag；提交前离线测试已通过。

## 11. Review 清单与操作

```bash
git status --short --branch
git diff --stat
git diff
git diff --cached
git ls-files --others --exclude-standard
git diff --check
```

`git diff` 不包含 untracked 内容。必须逐个读取新增测试、helper、契约文档及计划，对比第 7 节；不要遗漏原本未跟踪的需求目录。对每条生产代码改动回答：

1. 是否把敏感数据藏入 logging args、exception 或 response repr，而不仅是可见文本？
2. 是否通过删除日志表达式改变 JSON 解析、异常或返回路径？
3. 是否改变用户可见的 API/CLI 行为？批准依据是什么？
4. 测试保护是否真的覆盖收集和子进程？是否只靠空凭证或 skip？
5. CI、tox 和 doctest 是否仍存在触发真实请求的入口？

最终报告列出实际修改文件、实际执行命令/退出结果、验收项状态、B1 结论、风险及后续阶段工作。

## 12. 回滚策略

### 12.1 提交与回滚单位

建议拆成可独立审查的小提交：

1. 契约文档、测试离线底座、live 测试替换、CI/tox 凭证隔离作为安全基础提交。
2. core/CLI 敏感日志整改及相关回归。
3. logging 全局副作用修复及回归。
4. B1 批准后的 CLI stdout 例外可独立提交；最终文档/验收记录随对应改动更新。

每次提交前运行适用离线检查；不提交尚会运行 live 测试的中间状态。

### 12.2 触发回滚或停止合并的条件

- 任一签名、请求数据、返回结构、异常传播或订单调用次数发生非批准变化。
- 测试绕过 guard，出现任何实际外部连接尝试或依赖真实账户。
- 敏感哨兵泄漏，或宿主日志 handler 被移除/关闭/重复添加。
- CLI stdout 在 B1 未批准时被修改。
- CI 缺账户 Secret 就无法运行离线测试，或 tox 仍透传账户值。

### 12.3 执行方式

- 优先修复或撤销导致回归的最小逻辑块；未提交改动只恢复确认属于本次的对应片段，不能 `git reset --hard` 或 `git clean` 清理用户工作。
- 已提交改动使用定向 `git revert <commit>`，不得撤销既有需求文件或其他用户改动。
- 回滚生产日志/CLI 变更时，保留测试网络阻断、live 测试替换、CI 凭证移除及相应回归；不能通过关闭测试或恢复真实账户使旧行为“验证通过”。
- 回滚若会恢复敏感日志，不得把该状态标为安全验收通过；先暂停合并/发布，保留失败测试记录，修复后重新验收。
- 不恢复 GitHub 交易账户 Secrets 注入；仓库设置中的 Secrets 是否存在由维护者独立核实，不在本计划中读取或操作。
- 回滚后运行契约、日志和离线安全测试，重新审查 tracked/untracked；记录原因、受影响提交、遗留风险。

## 13. 风险、假设和阻断因素

| 编号 | 类型 | 事实/假设 | 处理与解除条件 |
| --- | --- | --- | --- |
| B1 | 决策阻断 | CLI stdout 明文回显有现有测试契约 | 需明确批准取消回显，或负责人明确接受残余风险及验收边界；未决定不能完整收口 |
| B2 | 执行权限 | 当前会话为 Plan 模式，不能改源码或写仓库计划路径 | 用户切换到 Build 后执行；当前只保存允许目录中的计划 |
| B3 | 环境条件未验证 | 未核实本地 Python 3.11、tox、OCR 包和离线依赖是否齐备 | Build 前确认依赖；缺失如实报告，测试不得临时依赖网络 |
| R1 | 已知兼容风险 | login/create_order 的日志表达式执行 JSON 解析 | 分离必要求值与日志，契约测试固定异常和调用顺序 |
| R2 | 已知行为缺陷 | 裸 raise、验证码递归、全局 session/token、导入时 OCR 初始化 | P0 不顺便修复；测试使用有限 fake，后续阶段另立需求 |
| R3 | 测试隔离风险 | package/doctest 收集和 CLI 子进程可早于函数级 fixture | 收集前 bootstrap、子进程独立保护、专门负向回归 |
| R4 | 日志范围边界 | 用户或第三方库可能自行记录请求/返回数据 | 不更改全局 logger 进行掩盖；准确描述 emtl 自身输出保证 |
| R5 | 线上协议未知 | 未调用真实券商；源码不定义完整 JSON schema | 仅固化已知透传契约，合成数据不宣称线上协议保证 |
| R6 | 环境与工具行为 | tox/pre-commit/构建可能下载依赖、修改文件；docs linkcheck 联网 | 分离准备和验收；记录生成 diff；离线阶段禁网并避免 linkcheck |
| R7 | 配置权限边界 | 仅读取 workflow，未验证 GitHub 后台是否存在账户 Secrets | 代码消除引用；维护者可单独删除闲置 Secrets，无需暴露值 |
| R8 | 文档归属 | `docs/refactor/` 在初始工作区未跟踪 | 逐文件审查、保留已有需求，显式选择提交文件 |

### 执行假设

- 当前获准阶段只有 P0，没有批准账户架构、重试或 Python 版本迁移。
- 删除敏感日志和 root logging 强制配置属于 P0 明确要求的行为调整；其他可观察变化必须有独立依据。
- 自动测试只使用合成 HTTP/OCR/账户数据；网络隔离用于防止意外请求，不将 Python monkeypatch 宣称为抵御恶意代码的系统沙箱。
- 默认测试入口从仓库根目录执行；显式受支持入口也必须实际验证 bootstrap 顺序。

## 14. 本次 Plan 已验证与待执行事项

**已验证：** 阅读所有 P0 指定文件、所有现有测试、三个 workflow、tox/pytest/打包配置及相关文档；核对 HEAD 和初始未跟踪文件；用不导入 emtl 的 AST 分析确认 9 个包级导出、core/utils/CLI 签名和 10+1 个现有测试。

**尚未执行：** 任何生产代码修改、契约/离线/日志测试编写、pytest/tox/lint、CLI 运行、依赖安装、OCR 初始化、CI 运行和任何真实券商请求。

**下一步：** 审批本计划与 B1；切换 Build；按 S0–S6 顺序实施；将批准的计划归档到 `docs/refactor/plans/P0-plan.md`，在最终报告中用实际测试结果完成验收矩阵。

## 15. Build 执行记录（未完全验收）

- 用户要求实施获批 P0 计划；B1 未获单独决定，保留 CLI stdout 兼容行为，完整验收仍阻断。
- 已添加测试收集前网络隔离和假 OCR、替换现有 live 测试、清理敏感日志、移除交易账户 CI 注入及 root logger 配置；未改真实交易 API 调用方式。
- 本地 `.venv` 缺 pytest，使用本机另一个 Python 3.11 环境的 pytest 9.2.0，通过 `PYTHONPATH` 显式复用并禁用第三方插件自动加载；默认入口与 `--pyargs emtl` 各 34 项通过。生产日志改动前契约/核心/CLI 基线 21 项通过；日志回归在旧实现先失败、修改后通过。
- 偏差及未完成：tox、pytest-cov、Black 在当前环境不可用，未运行 tox 覆盖率或 Black；未验证实际 tox 环境中的账户变量隔离。CLI 测试使用受保护的 `runpy` 模块入口、包元数据及安装的 `emt` 脚本；没有无保护地直接执行 CLI。未运行 Sphinx HTML 构建、CI 或真实券商验证。
- 使用缓存中的 Ruff 0.17.1 检查测试、CLI、utils 通过；全量检查报告既有 `__all__` 顺序和 `_check_resp` 裸 raise，均依兼容性要求保留。未使用计划指定版本验证。
- 测试矩阵尚非完整证明：收集前隔离、默认及包入口已有测试，但未对所有可能的子进程和传输方式作穷尽验证；日志测试使用合成哨兵，不能证明第三方 HTTP 日志或调用者自行打印不泄密。
- 没有 commit、push、publish 或 tag。余项：获得 B1 决策；在备齐本地依赖的 Python 3.11 环境运行计划的完整 tox/覆盖率、格式、文档和入口测试并补齐缺口；完成逐项验收后再判断 P0 完成。

## 16. Review FAIL 针对性修复授权与执行顺序

本节记录用户明确批准的五项修复，覆盖前文冲突处，不重新规划 P0，不扩展到 P1/P2。

1. B1 已解除：删除 CLI 凭证明文回显；保留参数、正常退出码及既有不执行登录/交易的行为；stdout/stderr/log 负向测试和契约同步更新。
2. 必须交付 `docs/refactor/requirements/P0.md`、本计划及 `docs/refactor/contracts/P0-public-api.md`；检查全局 ignore，不修改全局 Git 配置；允许仅对已审查的上述文档显式暂存。
3. 先在独立外层断网和假 OCR 下复现仓库外 `--pyargs` 的前置导入，再将 `src/emtl/tests/` 全部迁移为根目录 `tests/`；更新根 conftest、测试导入、pytest/tox 配置及相关文档。删除 `--pyargs emtl` 支持声明，不引入插件框架；验证仓库根和仓库外显式测试路径。
4. 将验证码日志回归拆为独立测试，只 mock HTTP/OCR 等依赖，真实执行非法 OCR 后恢复路径，断言调用次数、结果及安全日志；添加 URL、Cookie、Authorization 和响应哨兵。登录场景也以假 HTTP/OCR 执行验证码原函数。
5. 准备 Python 3.11 测试工具，与离线验收分开；在独立操作系统网络隔离下运行 pytest、tox 覆盖率、格式检查及虚构父账户环境穿透验证；记录命令、版本、退出码和失败原因。

仅新增必要的测试、验证记录及配置改动；生产交易实现不再调整。修复完成后停止，不 commit/push/tag/release。

## 17. 针对性修复结果与可复现证据

### 五项处理状态

| Review 问题 | 本次处理 | 状态 |
| --- | --- | --- |
| CLI 凭证回显 | 删除 print；正常 stdout 为空，stderr/log 无账户哨兵；参数、退出码、Python 登录语义不变 | 已修复，B1 已获批准 |
| 文档遗漏 | 当前全局 ignore 已不含 `docs/refactor/`，未修改全局配置；下列三文件已显式暂存，契约下载目标测试通过 | 已修复 |
| 防护晚于包导入 | 先在仓库外复现失败，再迁移至根 `tests/`，删除包内测试和 `--pyargs` 声明；仓库外显式路径全套通过 | 已修复 |
| OCR 假覆盖 | 所有测试不再替换 `_get_captcha_code`；独立错误恢复测试验证两次 GET/OCR、最终验证码及固定错误日志；增加 URL/Cookie/Authorization/body 哨兵 | 已修复 |
| CI 等价验证 | 实际 tox 环境在操作系统断网沙箱内通过；账户、NETRC 和 SSH 代理穿透负向验证；CI 指定版本格式检查通过 | 本地证据已补齐，远端 CI 未运行 |

必须纳入 Git 的三份文档（不批量强制添加其他文件）：

- `docs/refactor/requirements/P0.md`：需求条款未修改，仅删除暂存检查发现的末尾多余空行。
- `docs/refactor/plans/P0-plan.md`：原批准计划及本次追加授权/执行记录。
- `docs/refactor/contracts/P0-public-api.md`：契约及获批 CLI/测试入口变化。

`docs/reference/emtl.rst` 的 `../refactor/contracts/P0-public-api.md` 目标存在，并有自动回归检查。实际初始 `git check-ignore -v` 返回 1（无匹配），读取当前 `/Users/lld/.gitignore_global` 确认不再包含该目录规则；这与上次 Review 时的环境不同，非本次修改结果。

### 验证环境与命令

工作目录默认 `/Users/lld/emtl`。Python 3.11.14；pytest 9.2.0；pytest-cov 7.1.0；coverage 7.17.2；tox 4.67.12；Ruff 0.4.1；Black 24.4.0；uv 0.10.6。Ruff/Black 与 `.pre-commit-config.yaml` 一致，不再复用其他项目的 pytest，不再禁用插件自动加载。

依赖准备与离线测试明确分开：

```bash
uv pip install --offline --python .venv/bin/python pytest pytest-cov tox 'black==24.4.0' 'ruff==0.4.1' setuptools-scm
uv pip install --python .venv/bin/python pytest pytest-cov tox 'black==24.4.0' 'ruff==0.4.1' setuptools-scm
TOXPYTHON="$PWD/.venv/bin/python" .venv/bin/python -m tox -e py311-cover --notest -v
```

退出码分别为 1、0、0。首条失败原因是 Black wheel 不在离线缓存；后两条为联网的工具/构建依赖准备，没有运行测试或调用券商。

独立防护采用 macOS 的 `sandbox-exec -p '(version 1)(allow default)(deny network*)'`，拒绝网络且继承到子进程，不依赖被测 Python monkeypatch。先验证独立沙箱：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -B -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))'
```

退出码 1，预期的 `PermissionError: [Errno 1] Operation not permitted`，证明操作系统阻断连接；未访问外部服务。

迁移前，从批准临时目录运行同一沙箱下的 Python 脚本：先将 `ddddocr.DdddOcr` 替换为仅用于观察导入顺序的 `ReviewOcr`，再 `pytest.main(['-p', 'no:cacheprovider', '-c', '/dev/null', '--pyargs', 'emtl.tests.test_test_safety', '-k', 'bootstrap_was_installed_before_collection', '-q', '--tb=short'])`。退出码 1，`COLLECTION_OCR` 为 `ReviewOcr` 而不是 `FakeOcr`。此失败先于本次迁移，明确复现了 Review 发现的问题；现在不再支持该包测试入口。

正式离线验收命令：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest -q
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_logging_safety.py::test_captcha_invalid_ocr_recovers_without_leaking -q

TOXPYTHON="$PWD/.venv/bin/python" EM_USERNAME=P0_FAKE_PARENT_USER EM_PASSWORD=P0_FAKE_PARENT_PASSWORD P0_FAKE_ACCOUNT_CREDENTIAL=P0_FAKE_SECRET NETRC=P0_FAKE_NETRC SSH_AUTH_SOCK=P0_FAKE_SSH_SOCKET SSH_AGENT_PID=P0_FAKE_AGENT PIP_NO_INDEX=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m tox -e py311-cover -v --result-json .tox/P0-result.json

.venv/bin/ruff check src/emtl tests conftest.py
.venv/bin/black --check src/emtl tests conftest.py
git diff --check
```

以上退出码均为 0。默认 pytest 41 项通过，独立验证码测试 1 项通过，真实 tox 命令执行 `commands_pre` 账户隔离断言后 41 项通过。格式检查曾因两个 fixture 无返回值命名、测试代码排版及虚构密码关键字触发失败，针对性修复后以上最终检查通过；未修改生产交易接口以规避 lint。

另从 `/private/var/folders/0k/2wdc58817qj3v6mcyst_x6ww0000gn/T/opencode` 执行：

```bash
sandbox-exec -p '(version 1)(allow default)(deny network*)' /Users/lld/emtl/.venv/bin/python -m pytest /Users/lld/emtl/tests -q
```

退出码 0，全套 41 项通过。`test_checkout_entry_from_outside_repository` 也在新进程/临时工作目录中设置虚构父账户变量，验证收集前已清除凭证并安装假 OCR。

文档仅使用 `git add -- docs/refactor/requirements/P0.md docs/refactor/plans/P0-plan.md docs/refactor/contracts/P0-public-api.md` 显式暂存，`git ls-files --stage docs/refactor` 确认三者均在 index。首次 `git diff --check --cached` 因原需求末尾空行退出 2；仅清理这一文档空行后重新检查。未强制添加任何未知文件。

### 覆盖率、配置与剩余边界

- `coverage.xml` 由实际 tox 命令生成；总体含分支计分为 **84.42%**。`core.py` 125 条语句全部执行，含分支计分 **94.27%**；`_get_captcha_code` 的 12 条语句全部执行，非法 OCR 后恢复路径已有明确调用次数断言。
- JSON 覆盖率检查命令：`.tox/py311-cover/bin/python -m coverage json -o .tox/P0-coverage.json`，退出码 0；读 JSON 断言 `core.py` 的 `missing_lines == []`。未把未测的空 OCR 分支、工具函数、子进程入口或生成版本文件伪称为已全部覆盖。
- `tox c -e py311-cover -k pass_env set_env` 揭示 tox 默认还会透传 NETRC/SSH 代理变量，因此使用 `disallow_pass_env` 明确拒绝 `EM_*`、`NETRC`、`SSH_AUTH_SOCK`、`SSH_AGENT_PID`；保留必要的系统/安装工具默认变量，不宣称净化任意第三方凭证。为避免旧 tox 静默忽略安全配置，仅将测试工具最低版本设置为 4.67，没有迁移生产依赖或 Python 支持范围。
- 通过虚构父环境和 `commands_pre` 实际断言证明上述变量不进入测试（EM 用户名/密码由 setenv 置空）。不读取或输出真实账户值。
- tox 构建按原 setuptools-scm 设置重新生成被忽略的 `src/emtl/_version.py` 为 dirty 开发版；没有将其纳入 Git，也没有改动包级 `emtl.__version__ = "0.2.6"` 或进行发布。
- 额外静态 AST 对照确认 core/utils/CLI 公共函数签名与 HEAD 一致。除获批 CLI 输出外，本次未继续修改生产 core/utils 逻辑，未新增下单/撤单重试。
- 未执行 GitHub Actions/Linux、Sphinx/linkcheck 或 `tox -e check` 的自动修复型 pre-commit 流程；直接使用 CI 固定版本 Ruff/Black 检查了全部生产源码、迁移后的测试及根 conftest。没有调用真实券商、初始化真实 OCR、使用真实账户或进行实盘验证。
- 本次五项修复可提交下一次独立 P0 Review；这不是代替独立审查的 PASS 声明。既有全局会话/认证并发问题仍按原计划延期。完成后停止，不进入下一阶段。
