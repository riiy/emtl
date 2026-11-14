====
emtl
====

版本 ``0.3.0`` 的计划支持范围为 Linux / CPython 3.11。
公开函数签名、成功返回值及 CLI 参数与退出码遵循以下契约；
新增功能需补充契约测试，废弃接口需提供变更记录和迁移说明。
删除或不兼容修改必须另行批准并确定版本策略，P4 未授权删除既有接口。

- :download:`P0 旧版公共 API 契约 <../refactor/contracts/P0-public-api.md>`
- :download:`P2 独立账户客户端契约 <../refactor/contracts/P2-client-api.md>`
- :download:`P3 交易结果不确定性与异常契约 <../refactor/contracts/P3-trade-errors.md>`

当前导出的接口
==============

``emtl.__all__`` 包含九个旧模块级函数和 ``TradingClient``。
旧接口直接引用 ``emtl.core`` 的对应函数，保留共享会话与令牌的
历史行为；参见上述 P0 契约。

同步独立账户客户端 ``TradingClient`` 提供：

- ``login(duration=30)``、``close()``
- ``query_asset_and_position()``、``query_orders()``、``query_trades()``
- ``query_history_orders(size, start_time, end_time)``
- ``query_history_trades(size, start_time, end_time)``
- ``query_funds_flow(size, start_time, end_time)``
- ``get_last_price(symbol_code, market)``
- ``create_order(stock_code, trade_type, market, price, amount)``
- ``cancel_order(order_str)``

``TradeOutcomeUnknown`` 与 ``BrokerHTTPError`` 位于
``emtl.errors``，并未从包根目录通过 ``__all__`` 导出。
它们适用于 P3 约定的显式客户端，不适用于旧模块级交易接口。
实际使用方式与交易风险说明参见 :doc:`../usage`。

.. testsetup::

    from emtl import *

.. automodule:: emtl
    :members:
    :undoc-members:
    :special-members: __init__, __len__
