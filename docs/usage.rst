=====
Usage
=====

To use the project:
下面是登录、查询资产、下单、撤单的使用方法，具体使用请查看Reference

.. code-block:: python

    import emtl
    emtl.login("P0_FAKE_USER", "P0_FAKE_PASSWORD")
    asset = emtl.query_asset_and_position()
    print(asset)
    resp = emtl.create_order("FAKE_STOCK", "B", "SA", 5.01, 100)
    resp = emtl.cancel_order("P0_FAKE_ORDER")

以上仅为人工调用示例，参数为虚构值；实际调用可能产生真实交易，切勿在自动测试中运行。
自动测试使用离线替身，不连接券商。CLI 安全修复已取消凭证回显，参数和正常退出码保持不变；CLI 仍只解析参数，不执行登录或交易。
