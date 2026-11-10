========
使用指南
========

默认 HTTP Session 下的 Python API 可能连接真实券商。
本页示例仅供获得授权后的人工操作，不可直接放入 CI。
自动测试必须使用虚构账户和隔离的 HTTP/OCR 替身，禁止真实下单。

独立账户 TradingClient
======================

多账户场景优先使用 ``emtl.TradingClient``。创建客户端时必须显式传入
``username``，不自动读取 ``EM_USERNAME``；省略 ``password``
时，会在构造期间读取一次环境变量 ``EM_PASSWORD``。
每个实例独立持有 Session、Cookie 和认证令牌。

同一规范化用户名的客户端操作在单进程内串行，不同账户可以并行；
这不保证跨进程或跨设备的账户串行。
用完请在 ``finally`` 中调用 ``close()``；当前不提供上下文管理器或异步接口。

以下为 **仅限人工运行** 的登录和只读订单查询示例。
使用默认 Session 时仍会发起真实网络请求，不应出现在自动化测试中。

.. code-block:: python

    import os

    from emtl import TradingClient

    client = TradingClient(os.environ["EM_USERNAME"])
    try:
        if client.login() is None:
            raise RuntimeError("authentication required")
        orders = client.query_orders()
    finally:
        client.close()

``login(duration=30)`` 在认证证据满足条件时返回非空 token；
证据不足则返回 ``None``，传输或解析等异常可能原样传播。
新建客户端首次执行受保护的操作时可尝试自动登录一次。
登录失败后，如需恢复，必须显式再次调用 ``login()``。
``get_last_price(symbol_code, market)`` 不会自动登录。

下单、撤单与不确定结果
======================

``TradingClient.create_order(stock_code, trade_type, market, price, amount)``
和 ``TradingClient.cancel_order(order_str)`` 可能提交真实交易或撤单。
客户端对每次业务调用最多尝试一次交易 POST；不会自动重发、
补单、对账或补偿。请不要根据超时等异常推定交易一定失败。

- ``emtl.errors.TradeOutcomeUnknown``：已进入交易 POST 尝试边界，
  但结果无法确认。``operation``、``reason``、``status_code``
  只描述本地失败阶段，不能证明请求已送达、券商受理、成交或拒绝。
  **不得因该异常自动重发订单。**
- ``emtl.errors.BrokerHTTPError``：显式客户端的非交易请求收到
  有效整数状态码且不为 200；认证、查询等其他异常可能继续原样传播。

正常返回也不构成成交证明：订单 JSON 和撤单文本不会按真实券商业务状态
进行验证。具体边界见 :doc:`reference/emtl` 和其中链接的 P2/P3 契约。

旧版模块级接口
==============

``emtl.login()``、``emtl.query_asset_and_position()``、
``emtl.query_orders()``、``emtl.create_order()``、
``emtl.cancel_order()`` 等函数仍可调用，以维持兼容。
它们共用旧模块级 Session/认证令牌，不具备 ``TradingClient``
的账户隔离和新增交易异常保证，不能据此做并发多账户切换。
既有签名、返回值及其他兼容行为以 P0 公共 API 契约为准。

命令行接口
==========

``emt`` 和 ``python -m emtl`` 目前只解析命令行参数并退出。
虽然接受 ``--buy``、``--sell``、``--query`` 等参数，
``emtl.cli.run()`` **不会** 实际登录、查询券商或提交订单。

.. code-block:: console

    emt --help
    python -m emtl --help
