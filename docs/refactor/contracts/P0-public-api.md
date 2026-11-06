# P0 公共 API 契约

基于 `89328a75ea42362587fb46e6a9f395d0ca90ee86` 的静态源码；合成测试数据不代表完整券商协议。

## 包级导出

`__all__` 顺序为 `login`, `query_asset_and_position`, `query_orders`, `query_history_orders`, `query_trades`, `query_history_trades`, `query_funds_flow`, `create_order`, `cancel_order`。这些名称直接引用 `emtl.core` 的同名函数。

| 签名 | 行为 |
| --- | --- |
| `login(username: str = "", password: str = "", duration: int = 30) -> Optional[str]` | 空用户名或密码分别从 `EM_USERNAME` / `EM_PASSWORD` 回退；成功返回提取并 strip 的验证令牌；找不到令牌或捕获 KeyError 时返回 None。 |
| `query_asset_and_position()` | 真值 response 的 JSON 原样返回，否则 None。 |
| `query_orders()` | 同上。 |
| `query_trades()` | 同上。 |
| `query_history_orders(size, start_time, end_time)` | 同上。 |
| `query_history_trades(size, start_time, end_time)` | 同上。 |
| `query_funds_flow(size, start_time, end_time)` | 同上。 |
| `create_order(stock_code, trade_type, market: str, price: float, amount: int)` | 真值 response 的第二次 JSON 解析结果原样返回，否则 None；不会自动重试。 |
| `cancel_order(order_str: str)` | 输入 strip 后发送；真值 response 返回 strip 后的文本，否则 None。 |

查询和下单的 JSON 不验证类型或业务状态；通常为 dict，但不保证 schema。已有令牌时复用，否则自动调用 `login()`。默认查询表单为 `qqhs=100, dwc=""`；历史查询额外传 `st`、`et`。下单传 `stockCode/tradeType/zqmc/market/price/amount`，`zqmc` 为空。HTTP 非 200 当前执行裸 `raise`，普通调用中产生 RuntimeError；P0 不改变它。

## 其他既有调用面

- `emtl.core.get_last_price(symbol_code: str, market: str) -> float`：行情状态缺失或非零时返回 NaN，否则转换 `realtimequote.currentPrice`。
- `emtl.utils.get_logger(name)`：返回命名 logger；P0 移除原先强制重配 root logger 的副作用。
- `emtl.utils.emt_trade_encrypt(content: str) -> str`、`double_equal(a, b) -> bool`、`get_float(data: dict, key: str) -> float`、`get_int(data: dict, key: str) -> int` 保留签名和行为。
- `emtl.cli.run(args=None)`、`emt`、`python -m emtl` 保留入口、参数、互斥项和正常退出码 0。经用户明确批准，P0 安全修复取消原先的 `用户名 密码\n` 标准输出；正常调用现在不产生 stdout，也不在 stderr/log 回显凭证。CLI 仍只解析参数，不执行登录或交易；Python `login()` 的环境变量回退、请求和返回语义不变。

## 测试入口的批准调整

自动测试迁移到仓库根 `tests/`，不随 `emtl` 包分发。使用 `python -m pytest`、`python -m pytest tests`，或在仓库外显式传 checkout 的 `tests/` 路径。删除原先不安全的 `pytest --pyargs emtl` 测试入口声明；不要用包收集方式运行生产模块。此调整不删除任何公共交易 API。
