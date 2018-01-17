#!/usr/local/bin/python
#coding=utf-8
#下载股票历史数据
import os
import urllib2
import datetime
from datetime import date
import time
from matplotlib.cbook import iterable
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import copy_reg
import urllib
import re

# def queryAllStock():
#     url = 'http://quote.eastmoney.com/stock_list.html'
#     u = urllib.urlopen(url)
#     htmlstr = u.read()
#     group = re.match('(.*)', htmlstr).group()
#     print group
    
# 下载所有A股数据
# listAll ：股票代码
def downloadAllHistoryAShareData(listAll):
    # os.path.pardir: 上级目录
    downloadDir = os.path.pardir + '\stockdata' 
    stockDownload = StockDownload(downloadDir, date(2016,6,1), date.today())
    
#     listSS = range(600000, 604000)
#     listSZ = range(000000, 004060)
#     listAll = listSS + listSZ
#     listAll = ['000725','000783','002167','002505','002600','300315','600000','600011','600048','601001']

    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    startTime = time.clock()
    stockDownload.download_mutli(listAll, 'yahoo')
    
    endTime = time.clock()
    print '多线程执行时间:', (endTime-startTime)
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    
#     print '单线程执行开始:'
#     startTime = time.clock()
#     for i in listAll:
#         stockDownload.download(str(i))
# 
#     endTime = time.clock()   
#     print '单线程执行时间:', (endTime-startTime)

     
    
# 股票下载类，单只股票
class StockDownload:
    
    # 构造
    def __init__(self, downloadDir, startDate=date(2016,1,1), endDate=date.today()):
        #self.stockCode = stockCode
        self.downloadDir = downloadDir
        self.startDate = startDate
        self.endDate = endDate
        self.ignorelist_file = 'IgnoreListStock.txt'
        
        #增加忽略列表
        if os.path.exists(self.downloadDir) == False:
            os.makedirs(self.downloadDir)
        try:    
            f = open(self.downloadDir + '\\' + self.ignorelist_file)
            data = f.read()
            self.ignoreList = data.split('\n')
            f.close()
        except Exception as e:
            print str(e)
            self.ignoreList = []

    # 多线程下载
    def download_mutli(self, listSockeCode, source='yahoo'):
        pool = ThreadPool(processes=5)
        if source == 'yahoo':
            pool.map(self.downloadFromYahoo, listSockeCode)

        elif source == '163':
            pool.map(self.downloadFrom163, listSockeCode)      
        pool.close()
        pool.join()  
    
    # 从雅虎API下载    
    def downloadFromYahoo(self, stockCode):
        stockCode = str(stockCode).zfill(6)  #不足6位，前面补零
        
#         if stockCode in self.ignoreList:
#             print 'ignore:', stockCode
#             return;
        
        if os.path.exists(self.downloadDir) == False:
            os.makedirs(self.downloadDir)
        stock_file = self.downloadDir + '/' + stockCode + '.csv'
        #print stockCode
        
#         if os.path.exists(stock_file):
#             print (">>exist:" + stockCode)
#             return
        
        print (">>download begin:" + stockCode)
        
        exchange = "SS" if (int(stockCode) // 100000 == 6) else "SZ"
    
        if iterable(self.endDate):
            d1 = (self.startDate[1]-1, self.startDate[2], self.startDate[0])
        else:
            d1 = (self.startDate.month-1, self.startDate.day, self.startDate.year)
        if iterable(self.endDate):
            d2 = (self.endDate[1]-1, self.endDate[2], self.endDate[0])
        else:
            d2 = (self.endDate.month-1, self.endDate.day, self.endDate.year)
    
        g='d'
    
        ticker = stockCode + '.' + exchange
        urlFmt = 'http://ichart.yahoo.com/table.csv?a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&s=%s&y=0&g=%s&ignore=.csv'
    
        url =  urlFmt % (d1[0], d1[1], d1[2],
                         d2[0], d2[1], d2[2], ticker, g)
    
        if(not self.down_file(url, stock_file)):
            self.downloadFrom163(stockCode)
        print (">>download finish："  + stockCode)
    
    # 从网易API下载    
    def downloadFrom163(self, stockCode):
        stockCode = str(stockCode).zfill(6)  #不足6位，前面补零
        
        stockCode163 = stockCode
        if int(stockCode) // 100000 == 0:
            stockCode163 = '1'+stockCode
        else:
            stockCode163 = '0'+stockCode    
        
#         if stockCode in self.ignoreList:
#             print 'ignore:', stockCode
#             return;
        
        if os.path.exists(self.downloadDir) == False:
            os.makedirs(self.downloadDir)
        stock_file = self.downloadDir + '/' + stockCode + '.csv'
        #print stockCode
        
#         if os.path.exists(stock_file):
#             print (">>exist:" + stockCode)
#             return
        
        print (">>download begin:" + stockCode)
        
        strDateStart = self.startDate.strftime('%Y%m%d')
        strDateEnd = self.endDate.strftime('%Y%m%d')
    
        urlFmt = 'http://quotes.money.163.com/service/chddata.html?code=%s&start=%s&end=%s'
    
        url =  urlFmt % (stockCode163,strDateStart, strDateEnd)
    
        self.down_file(url, stock_file)

        print (">>download finish："  + stockCode)
          
    # url:下载路径
    # file_name:保存到本地的文件名   
    # 找不到股票代码则放入忽略列表 
    def down_file(self,url, file_name):
    
        try:
            u = urllib2.urlopen(url)
            f = open(file_name, 'wb')
        
            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
            
                file_size_dl += len(buffer)
                f.write(buffer)
            f.close()
        except Exception as e:
            print str(e)
            
            # basename = os.path.basename(os.path.splitext(file_name)[0]) #股票代码
            #
            # f = open(self.downloadDir + '/' + self.ignorelist_file, 'a') # a，文件尾部插入，不覆盖原数据
            # f.write('\n' + basename)
            # f.close()
        finally:
            None        

#     def deleteFile(self,fileName):
#         try:
#             os.remove(self.stockCode + ".csv")
#         except Exception as e:
#             pass      


if __name__ == "__main__":
    listAll = ['000725', '000783', '002167', '002505', '002600', '300315', '600000', '600011', '600048', '601001']
    downloadAllHistoryAShareData(listAll)