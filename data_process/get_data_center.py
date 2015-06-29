#!/usr/local/bin/python
#coding=utf-8

import os
import datetime
import pandas as pd

import util.commons as cm
from util.stockutil import getSixDigitalStockCode
from data_to_sql import download_stock_kline
import tushare as ts


# 获取个股K线数据
# input:
# ->code: 股票代码
# output:
# -> DataFrame
def get_stock_k_line(code, date_start='', date_end=datetime.date.today()):
    code = getSixDigitalStockCode(code)
    fileName = 'h_kline_' + str(code) + '.csv'
    
    df = None
    #如果存在则直接取
    if os.path.exists(cm.DownloadDir+fileName):
        df = pd.read_csv(cm.DownloadDir+fileName)
    # 不存在则立即下载
    else:
        df = download_stock_kline(code, date_start, date_end)
    return df     

# 获取个股的基本信息：股票名称，行业，地域，PE等，详细如下
#     code,代码
#     name,名称
#     industry,所属行业
#     area,地区
#     pe,市盈率
#     outstanding,流通股本
#     totals,总股本(万)
#     totalAssets,总资产(万)
#     liquidAssets,流动资产
#     fixedAssets,固定资产
#     reserved,公积金
#     reservedPerShare,每股公积金
#     eps,每股收益
#     bvps,每股净资
#     pb,市净率
#     timeToMarket,上市日期
# 返回值类型：Series
def get_stock_info(code):
    try:
        df = pd.DataFrame.from_csv(cm.DownloadDir + cm.TABLE_STOCKS_BASIC + '.csv')
        #se = df.loc[int(code)]
        se = df.ix[int(code)]
        return se
    except Exception as e:
        print str(e)    

# 获取终止上市股票列表        
def get_stock_terminated():
    return ts.get_terminated()  

            