# -*- coding: utf-8 -*-
# ! /usr/bin/env python

"""
@author:LiWei
@license:LiWei
@contact:877129310@qq.com
@version:
@var:
@note:

"""

from scrapy_js_api.utils.date_parse import parse_date

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.proxy import ProxyType, Proxy
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import uuid
import datetime
import MySQLdb
import random
import json
import re

class Selenium_Spider(object):
    # 启动js渲染
    def __init__(self, debug, proxy, path):
        self.idx = 1
        self.debug = debug
        self.proxy = proxy
        self.uuid = uuid.uuid1().hex
        self.error_url = []
        self.path = path
        self.conf = self.load_conf()
        self.timeout = 10

    # 加载配置文件
    def load_conf(self):
        with open(self.path, "rb") as f:
            conf = f.read()
        return json.loads(conf)

    # 添加代理
    def open_proxy(self):
        self.proxies = webdriver.common.proxy.Proxy()
        self.proxies.proxy_type = ProxyType.MANUAL
        # 加载代理
        path = self.load_conf().get("proxy").get("path")
        with open(path, 'rb')as f:
            proxy_list = f.readlines()
        # 随机添加
        proxy = random.choice(proxy_list)
        print u"随机切换代理ip:%s" % proxy
        self.proxies.http_proxy = proxy
        # 将代理设置添加到webdriver.DesiredCapabilities.PHANTOMJS中
        # self.proxies.add_to_capabilities(DesiredCapabilities.PHANTOMJS)
        # driver.start_session(DesiredCapabilities.PHANTOMJS)
        # 将代理设置添加到webdriver.DesiredCapabilities.FIREFOX中
        self.proxies.add_to_capabilities(DesiredCapabilities.FIREFOX)
        driver.start_session(DesiredCapabilities.FIREFOX)

    # 关闭js渲染
    def close_spider(self):
        driver.quit()
        print u"本次录入%s条数据!" % (self.idx - 1)

    # 获取时间
    def get_time(self, time_day):
        d1 = datetime.datetime.now()
        # 几天前的时间
        d2 = d1 - datetime.timedelta(days=time_day)
        day = datetime.datetime.strftime(d1, "%Y:%m:%d")
        today = datetime.datetime.strftime(d2, "%Y:%m:%d")
        return day, today

    # 构造URL
    def urllist(self):
        urllist = []
        day, today = self.get_time(self.conf.get("urllist").get("time_day"))
        pages = self.conf.get("urllist").get("pages")
        urls = self.conf.get("urllist").get("urls")
        rep = self.conf.get("urllist").get("rep")
        pg = self.conf.get("urllist").get("pg")
        if len(pages) == 0:
            for uri in urls:
                urllist.append(uri)
        else:
            for i in xrange(len(pages)):
                for page_index in xrange(pg, pages[i] + 1, 1):
                    urllist.append(urls[i].format(page_index=page_index, day=day, today=today))
                if rep != "":
                    urllist.append(urls[i].replace(rep, ""))
        return urllist

    # 列表解析
    def get_spider(self, urllist, net_spider_id):
        # 列表页
        for url in urllist:
            uris = []
            # 每隔20个请求随机切换代理
            if self.idx % 20 == 0 and self.proxy == True:
                self.open_proxy()
            try:
                print "url:%s" % url
                driver.get(url)
            except TimeoutException, e:
                print e
                self.timeout += 1
                if self.timeout == 100:
                    self.open_proxy()
                print u"已添加异常URL连接:%s" % url
                self.error_url.append(url)
                continue
            try:
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.XPATH, self.conf.get("list_page").get("xpath"))))
            except TimeoutException, e:
                print e
                self.idx += 1
                print u"已添加异常URL连接:%s" % url
                self.error_url.append(url)
                self.timeout += 1
                if self.timeout == 100:
                    self.open_proxy()
                continue
            urls = driver.find_elements_by_xpath(self.conf.get("list_page").get("xpath"))
            for uri in urls:
                uri = uri.get_attribute("href")
                uris.append(uri)
            # 详情页连接
            for ul in uris:
                # 每隔20个请求随机切换代理
                if self.idx % 20 == 0 and self.proxy == True:
                    self.open_proxy()
                try:
                    driver.get(ul)
                except TimeoutException, e:
                    print e
                    self.timeout += 1
                    if self.timeout == 100:
                        self.open_proxy()
                    continue

                try:
                    self.fields_item(net_spider_id)
                except NoSuchElementException, e:
                    print e
                    self.idx += 1
                    continue

    # 内容解析
    def fields_item(self, net_spider_id):
        self.items = {}
        self.fields = self.conf.get("fields")
        for k, v in self.fields.iteritems():
            if v.keys()[0] == "xpath":
                self.items[k] = driver.find_element_by_xpath(
                    v["xpath"].replace("//text()", "").replace("/text()", "")).text
            else:
                self.items[k] = v["value"]
        self.items['url'] = driver.current_url
        self.items['spider_jobid'] = self.uuid
        self.items['net_spider_id'] = net_spider_id
        self.pipelines(self.items)
        print u"{:=^30}".format(self.idx)
        if self.debug:
            for k, v in self.items.iteritems():
                print u"{:>13.13}:{}".format(k, v)
        else:
            self.mysql_db()
        self.idx += 1

    def pipelines(self, items):
        pass
        content = items["content"]


    # 入库
    def mysql_db(self):
        self.fields = []
        self.values = []
        mysql = self.conf.get("mysql")
        self.conn = MySQLdb.connect(host=mysql.get("host"), port=mysql.get("port"), user=mysql.get("user"),
                                    passwd=mysql.get("passwd"), db=mysql.get("db"),
                                    charset=u"utf8")
        self.cur = self.conn.cursor()
        for k, v in self.items.iteritems():
            self.fields.append(k)
            self.values.append(v)

        sql = u"INSERT INTO {}({}) VALUES({}) ON DUPLICATE KEY UPDATE ".format(mysql.get("tablename"),
                                                                               u",".join(self.fields),
                                                                               u','.join([u'%s'] * len(self.fields))),
        sql = str(sql[0])
        for f in self.fields:
            sql += u'{}=VALUES({}),'.format(f, f)
        sql = sql[:-1] + u';'
        try:
            self.cur.execute(sql, self.values)
            self.conn.commit()
            self.cur.execute(
                u"UPDATE {} SET update_date='{}' WHERE url='{}'".format(mysql.get("tablename"), datetime.datetime.now(),
                                                                        self.items[u'url']))
            self.conn.commit()
        except MySQLdb.Error, e:
            print (u"Mysql Error %d: %s" % (e.args[0], e.args[1]))
        print (u"数据插入/更新成功!")
        self.cur.close()
        self.conn.close()

    def run(self):
        crawl = Selenium_Spider(self.debug, self.proxy, self.path)
        global driver
        # 采用Firefox或PhantomJS引擎方式打开网页
        driver = webdriver.Firefox()
        # 请求等待10秒
        # WebDriverWait(driver, 10)
        # 隐式等待30秒
        driver.implicitly_wait(10)
        # 图片加载超时设置
        driver.set_page_load_timeout(10)
        # 脚本加载超时设置
        driver.set_script_timeout(10)
        if self.proxy:
            print u"代理状态启动!"
            self.open_proxy()
        else:
            print u"默认状态启动!"
        urllist = crawl.urllist()
        net_spider_id = self.conf.get("spiders").get("net_spider_id")
        crawl.get_spider(urllist, net_spider_id)
        crawl.close_spider()


if __name__ == '__main__':
    pass
    Selenium_Spider(debug=True, proxy=False, path="../configs/ccgp_gy.json").run()
    re.findall()