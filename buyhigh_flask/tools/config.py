BASE_URL = "https://stoyse.hackclub.app/"

API_LIST = {
    "stock_data": {
        "name": "Stock Data",
        "url": "stock-data",
        "description": "Fetches stock data from the API.",
        "status": True
    },
    "trade_buy": {
        "name": "Trade Buy",
        "url": "trade/buy",
        "description": "Endpoint for buying stocks.",
        "status": True
    },
    "trade_sell": {
        "name": "Trade Sell",
        "url": "trade/sell",
        "description": "Endpoint for selling stocks.",
        "status": True
    },
    "portfolio": {
        "name": "Portfolio",
        "url": "portfolio",
        "description": "Fetches portfolio data.",
        "status": True
    },
    "assets": {
        "name": "Assets",
        "url": "assets",
        "description": "Fetches asset data.",
        "status": True
    },
    "status": {
        "name": "Status",
        "url": "status",
        "description": "Checks the status of the API.",
        "status": True
    }
}