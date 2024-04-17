_urls: dict = {
    "yzm": "https://jywg.18.cn/Login/YZM?randNum=",
    "login": "https://jywg.18.cn/Login/Authentication?validatekey=",
    "query_asset_and_pos": "https://jywg.18.cn/Com/queryAssetAndPositionV1?validatekey=",
    "query_orders": "https://jywg.18.cn/Search/GetOrdersData?validatekey=",
    "query_trades": "https://jywg.18.cn/Search/GetDealData?validatekey=",
    "query_his_orders": "https://jywg.18.cn/Search/GetHisOrdersData?validatekey=",
    "query_his_trades": "https://jywg.18.cn/Search/GetHisDealData?validatekey=",
    "query_funds_flow": "https://jywg.18.cn/Search/GetFundsFlow?validatekey=",
    "query_positions": "https://jywg.18.cn/Search/GetStockList?validatekey=",
    "insert_order": "https://jywg.18.cn/Trade/SubmitTradeV2?validatekey=",
    "cancel_order": "https://jywg.18.cn/Trade/RevokeOrders?validatekey=",
}
_base_headers: dict = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36",
    "Origin": "https://jywg.18.cn",
    "Host": "jywg.18.cn",
}
