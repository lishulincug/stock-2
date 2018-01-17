#coding=utf-8
#!/usr/local/bin/python

import sys
sys.path.append('../')

import tushare as ts
import pandas as pd
import datetime
from multiprocessing.dummy import Pool as ThreadPool
from tushare.util import dateu as du
from tqdm import tqdm

from util import stockutil as util

from util.stockutil import fn_timer as fn_timer_

from init import *
from util.commons import *
from data_calcute import calcute_ma_all


###################################
#-- 获取股票基本信息       --#
############################
def download_stock_basic_info():
    
    try:
        df = ts.get_stock_basics()

        print df.columns
        df[KEY_CODE] = df.index
        df = df[[KEY_CODE,KEY_NAME, KEY_INDUSTRY, KEY_AREA, KEY_TimeToMarket]]

        print df.columns
        print df.head()

        sql = 'select code from {}'.format(STOCK_BASIC_TABLE)
        df_code = pd.read_sql(sql, engine)
        df = df[df['code'].apply(lambda x : not x in df_code['code'].get_values())]
        print df.head()
        print len(df)
        if len(df):
            df.to_sql(STOCK_BASIC_TABLE, engine, if_exists='append', index=False)

        # 添加指数
        # indexs = [('sh', '上证指数', '指数','全国','19910715'),
        #           ('sz', '深圳成指', '指数','全国','19940720'),
        #           ('hs300', '沪深300指数', '指数','全国','20050408'),
        #           ('sz50', '上证50指数', '指数','全国','20040102'),
        #           ('zxb', '中小板指数', '指数','全国','20050607'),
        #           ('cyb', '创业板指数', '指数','全国','20100531'),]
        # df = pd.DataFrame(indexs, columns=[KEY_CODE,KEY_NAME, KEY_INDUSTRY, KEY_AREA, KEY_TimeToMarket])
        # print df
        # df.to_sql(STOCK_BASIC_TABLE, engine, if_exists='append', index=False)

           
    except Exception as e:
        print str(e)        


# 下载单只股票到数据库
def download_stock_kline_by_code(code, date_start='', date_end=datetime.datetime.now()):
    
    try:
        # 设置日期范围
        if date_start == '':
            # 取数据库最近的时间
            sql = "select MAX({0}) as {0} from {1} where {2}='{3}'".format(KEY_DATE, STOCK_KLINE_TABLE, KEY_CODE, code)
            df = pd.read_sql_query(sql, engine)
            if df is not None and  df.ix[0, KEY_DATE] is not None:
                date_start = df.ix[0, KEY_DATE]
                date_start = datetime.datetime.strptime(str(date_start), "%Y-%m-%d") + datetime.timedelta(1)
                date_start = date_start.strftime('%Y-%m-%d')
            else:
                se = get_stock_info(code)
                date_start = se[KEY_TimeToMarket]
                date_start = datetime.datetime.strptime(str(date_start), "%Y%m%d")
                date_start = date_start.strftime('%Y-%m-%d')

        if isinstance(date_end, datetime.date):
            date_end = date_end.strftime('%Y-%m-%d')

        if date_start >= date_end:
            print 'Code:{0} is updated to {1}'.format(code, date_start)
            return

        # 开始下载
        # 日期分隔成一年以内
        dates = pd.date_range(date_start, date_end)
        df = pd.DataFrame(dates, columns=['date'])
        df['year'] = df['date'].apply(lambda x : x.year)
        print df.head()

        years = list(set(df['year'].get_values()))
        years.sort()

        for year in years:
            df1 = df[df['year']==year]
            if len(df) >= 2:
                date_s = str(df1['date'].get_values()[0])
                date_e = str(df1['date'].get_values()[-1])
                date_s = date_s[:10]
                date_e = date_e[:10]
            print 'download ' + str(code) + ' k-line >>>begin (', date_s + u' 到 ' + date_e + ')'
            df_qfq = download_kline_source_select(code, date_s, date_e)
            if len(df_qfq):
                df_qfq.to_sql(STOCK_KLINE_TABLE, engine, if_exists='append', index=False)
                print '\ndownload {} k-line to mysql finish ({} to {})'.format(code, date_s, date_e)
            else:
                return 'fail... , and try again'

    except Exception as e:
        print str(e)        
    
        
    # return None

# 下载源选择
def download_kline_source_select(code, date_start, date_end):
    try:
        if len(code)==6:
            df_qfq = ts.get_h_data(str(code), start=date_start, end=date_end) # 前复权
            df_hfq = ts.get_h_data(str(code), start=date_start, end=date_end, autype='hfq')  # 后复权
        else:
            # import pandas.io.data as web
            # price = web.get_data_yahoo('000001.SS', '1991-07-15')
            df_qfq = ts.get_hist_data(str(code), start=date_start, end=date_end)
        if len(df_qfq)==0 or (len(code)==6 and len(df_hfq)==0):
            return pd.DataFrame()
        #if df_qfq is None:
        #df_qfq = ts.get_hist_data(code, start=date_start, end=date_end)
        # df_qfq = df_qfq[::-1]
        df_qfq[KEY_CODE] = code
        df_qfq[KEY_DATE] = df_qfq.index


        columns = [KEY_CODE, KEY_DATE, KEY_OPEN, KEY_HIGH, KEY_CLOSE, KEY_LOW, KEY_VOLUME]
        df_qfq = df_qfq[columns]

        if len(code)==6:
            df_qfq['close_hfq'] = df_hfq['close']
        else:
            df_qfq['close_hfq'] = df_qfq['close']


        print df_qfq.head()

        return df_qfq
    except Exception as e:
        print str(e)
        return pd.DataFrame()
        
# 下载股票的历史分笔数据
# code:股票代码
# 默认为最近3年的分笔数据
def download_stock_quotes(code, date_start='', date_end=str(datetime.date.today())):
    code = util.getSixDigitalStockCode(code)
    try:
        if date_start == '':
            date = datetime.datetime.today().date() + datetime.timedelta(-365*3) 
            date_start = str(date)
          
        dateStart = datetime.datetime.strptime(str(date_start), "%Y-%m-%d")   
                
        for i in range(du.diff_day(date_start, date_end)):
            date = dateStart + datetime.timedelta(i)
            strDate = date.strftime("%Y-%m-%d")
            df = ts.get_tick_data(code, strDate)
            print df
    except Exception as e:
        print str(e)        

#######################
##  private methods  ##
#######################

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
        sql = "select * from %s where %s='%s'" % (STOCK_BASIC_TABLE, KEY_CODE, code)
        df = pd.read_sql_query(sql, engine)
        se = df.ix[0]
    except Exception as e:
        print str(e)
    return se

# 获取所有股票的历史K线
@fn_timer_
def download_all_stock_history_k_line():
    print 'download all stock k-line start'
    
    try:

        df = pd.read_sql_table(STOCK_BASIC_TABLE, engine)
        codes = list(df[KEY_CODE].get_values())
        print 'total stocks:{0}'.format(len(codes))
        # for code in codes:
        #     download_stock_kline_by_code(code)
        codes = codes[::-1]

        #codes = r.lrange(INDEX_STOCK_BASIC, 0, -1)
        pool = ThreadPool(processes=10)
        pool.map(download_stock_kline_by_code, codes)
        pool.close()
        pool.join()

    except Exception as e:
        print str(e)
    print 'download all stock k-line finish'
 

def check_unnormal_stock_price():
    """
    异常股价检测
    :return:
    """
    sql = "select code,name from stock_basic_all"
    df_code =  pd.read_sql(sql, engine)

    unnormal_codes = []
    for code,name in df_code[['code','name']].get_values():
        sql = "select code, date, close, close_hfq from hq_db.stock_kline_fq where code='{}' and date >'2002-12-06' order by date asc ".format(code)
        df = pd.read_sql(sql, engine)
        if len(df) < 2:
            continue
        # print code, len(df)
        df.index = df['date']
        returns_close = df['close'].pct_change()
        # returns_close_hfq = df['close_hfq'].pct_change()
        returns_close[0]= 0
        # returns_close_hfq[0] = 0

        # print returns_close_hfq[:10]

        df['returns_close'] = returns_close
        # df['returns_close_hfq'] = returns_close_hfq

        df1 = df[df['returns_close']==df['returns_close'].min()]
        # print df1

        #print '前复权', min(returns_close), '后复权',min(returns_close_hfq)
        if returns_close.min() < -0.2:
            print df1
            #先删除code对应的行情
            sql = "delete from stock_kline_fq where code='{}'".format(code)
            print sql
            engine.execute(sql)
            #再重新取
            download_stock_kline_by_code(code)

            # print ">"*10, name, code, '前复权', returns_close.min()
            unnormal_codes.append((name, code, '前复权', returns_close.min()))
        # if returns_close_hfq.min() < -0.15:
        #     print df1
        #     # print  ">"*10, name, code, '后复权', returns_close_hfq.min()
        #     unnormal_codes.append((name, code, '后复权', returns_close_hfq.min()))

    print "\n"*5
    for un_code in unnormal_codes:
        print "{}:{}\t{}\t{}".format(un_code[0], un_code[1], un_code[2], un_code[3])

    print "total count", len(unnormal_codes)

if __name__ == '__main__':

    download_stock_basic_info()
    download_all_stock_history_k_line()

    check_unnormal_stock_price()
    #calcute_ma_all()
    #download_stock_kline_to_sql('000002', date_start='1991-01-29',date_end='2012-12-16')
    
    #convertRedisToSqlite()

    


