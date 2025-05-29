=====
Usage
=====

To use the project:
下面是登录、查询资产、下单、撤单的使用方法，具体使用请查看Reference

.. code-block:: python

    import emtl
    emtl.login("2020123456789", "123456")
    asset = emtl.query_asset_and_position()
    print(asset)
    resp = create_order("000002", "B", "SA", 5.01, 100)
    resp = cancel_order("20240520_130662")
