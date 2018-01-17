#coding=utf-8
from trade_process.strategy import main

if __name__ == '__main__':
    stockList = ['000725', '000783', '002167', '002505', '002600', '300315', '600000', '600011', '600048', '601001']
    ChinaStockIndexList = [
        "000001",  # sh000001 上证指数
        "399001",  # sz399001 深证成指
        "000300",  # sh000300 沪深300
        "399005",  # sz399005 中小板指
        "399006",  # sz399006 创业板指
        "000003",  # sh000003 B股指数
        "000016",  # 上证50
        "000012",  # 国债指数
    ]
    main(ChinaStockIndexList)