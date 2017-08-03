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

from selenium import webdriver
from selenium.webdriver.common.proxy import ProxyType, Proxy
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import datetime, logging
import threading
import random, MySQLdb, json
from scrapy_js_api.utils.middlewares import mysql_spider, load_configs
from scrapy_js_api.utils.date_parse import parse_date


class Selenium_Spider(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        self.idx = 1
        self.mysql_config = load_configs()['mysql']
        super(Selenium_Spider, self).__init__()

    # 运行
    def run(self):
        while 1:
            logging.info(u"线程%d %s: 等待分配工作!" % (self.ident, self.name))
            self.task = self.queue.get(block=True)  # 接收消息
            if self.task["webdriver"].lower() == "phantomjs":
                self.driver = webdriver.PhantomJS()
                logging.info(u"启动:PhantomJS渲染引擎进行渲染!")
            else:
                self.driver = webdriver.Firefox()
                logging.info(u"启动:Firefox渲染引擎进行渲染!")
            # 隐式等待30秒
            logging.info(u"正在加载设置渲染引擎配置....")
            self.driver.implicitly_wait(10)
            # 图片加载超时设置
            self.driver.set_page_load_timeout(10)
            # 脚本加载超时设置
            self.driver.set_script_timeout(10)
            logging.info(u"渲染引擎配置设置成功!默认超时设置10s")
            self.name_spider_config = mysql_spider(self.task["name_spider"])
            self.debug = self.task["debug"]
            if self.name_spider_config['proxy'].lower() == "true":
                logging.info(u"代理状态启动!")
                self.open_proxy()
            else:
                logging.info(u"默认状态启动!")
            logging.info(u"启动任务:%s ,任务名:%s" % (self.task["spider_jobid"], self.task["name_spider"]))
            # 采集启动
            self.get_spider()
            logging.info(u"任务完成:%s ,任务名:%s" % (self.task["spider_jobid"], self.task["name_spider"]))
            # 关闭javascript渲染
            self.close_spider()
            self.queue.task_done()  # 完成一个任务
            res = self.queue.qsize()  # 判断消息队列大小
            if res > 0:
                logging.warning(u"还有 %d 任务要完成!" % res)

    # 代理配置
    def open_proxy(self):
        self.proxyip = webdriver.common.proxy.Proxy()
        self.proxyip.proxy_type = ProxyType.MANUAL
        # 加载代理
        self.conn = MySQLdb.connect(host=self.mysql_config.get("host", "localhost"),
                                    port=self.mysql_config.get("port", 3306),
                                    user=self.mysql_config.get("user", "root"),
                                    passwd=self.mysql_config.get("passwd", "root"),
                                    db=self.mysql_config.get("db"), charset=u"utf8")
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT proxyip FROM net_proxy;")
        self.proxies = self.cur.fetchall()
        self.proxy = random.choice(self.proxies)[0]
        self.cur.close()
        self.conn.close()
        # 随机添加
        logging.warning(u"随机切换代理ip:%s") % self.proxy
        self.proxyip.http_proxy = self.proxy

        if self.task["webdriver"].lower() == "phantomjs":
            # 将代理设置添加到webdriver.DesiredCapabilities.PHANTOMJS中
            self.proxyip.add_to_capabilities(DesiredCapabilities.PHANTOMJS)
            self.driver.start_session(DesiredCapabilities.PHANTOMJS)
        else:
            # 将代理设置添加到webdriver.DesiredCapabilities.FIREFOX中
            self.proxyip.add_to_capabilities(DesiredCapabilities.FIREFOX)
            self.driver.start_session(DesiredCapabilities.FIREFOX)

    # get_spider 采集器
    def get_spider(self):
        urls = self.name_spider_config["start_urls"].replace("\r\n", "").split(",")
        # 列表页循环
        for url in urls:
            uris = []
            try:
                self.driver.get(url)
            except TimeoutException, e:
                logging.error(e)
                continue
            try:
                wait = WebDriverWait(self.driver, 10)
                rules_listxpath = json.loads(self.name_spider_config["rules"])["rules"]["rules_listxpath"]
                wait.until(EC.presence_of_element_located((By.XPATH, rules_listxpath)))
            except TimeoutException, e:
                logging.error(e)
                continue
            if rules_listxpath[-3:] != "//a":
                rules_listxpath += "//a"
            elif rules_listxpath[-2:] != "/a":
                rules_listxpath += "/a"
            urllist = self.driver.find_elements_by_xpath(rules_listxpath)
            # 获得详情页列表
            for urll in urllist:
                urll = urll.get_attribute("href")
                uris.append(urll)
            for uri in uris:
                try:
                    self.driver.get(uri)
                except TimeoutException, e:
                    logging.error(e)
                    continue
                try:
                    self.fields_item()
                except NoSuchElementException, e:
                    logging.error(e)
                    continue

    # 内容解析
    def fields_item(self):
        pass
        self.items = {}
        fields = json.loads(self.name_spider_config["fields"])["fields"]
        for k, v in fields.iteritems():
            if v.keys()[0] == "xpath":
                self.items[k] = self.driver.find_element_by_xpath(
                    v["xpath"].replace("//text()", "").replace("/text()", "")).text
            else:
                self.items[k] = v["value"]
        self.items["url"] = self.driver.current_url
        self.items["pubtime"] = parse_date(self.items["pubtime"])
        if self.debug.lower() == "true":
            print u"{:=^30}".format(self.idx)
            for k, v in self.items.iteritems():
                print u"{:>13.13}:{}".format(k, v)
        else:
            self.mysql_db(self.items)
        self.idx += 1

    # 数据入库
    def mysql_db(self, items):
        pass
        fields = []
        values = []
        for k, v in items.iteritems():
            fields.append(k)
            values.append(v)
        self.mysql_config = load_configs()['mysql']
        self.conn = MySQLdb.connect(host=self.mysql_config.get("host"), port=self.mysql_config.get("port"),
                                    user=self.mysql_config.get("user"), passwd=self.mysql_config.get("passwd"),
                                    db=self.mysql_config.get("db"), charset=u"utf8")
        self.cur = self.conn.cursor()
        try:
            # 通过爬虫名称找表明
            self.cur.execute(
                u"SELECT  id,tablename FROM net_spider WHERE  spider_name='{}';".format(
                    self.name_spider_config["spider_name"]))
            TableName = self.cur.fetchall()
            if TableName:
                net_spider_id = TableName[0][0]
                TableName = TableName[0][1]
                # 添加net_spider爬虫id
                fields.append("net_spider_id")
                values.append(net_spider_id)

                # 根据 item 字段插入数据
                sql = u"INSERT INTO {}({}) VALUES({}) ON DUPLICATE KEY UPDATE ".format(TableName,
                                                                                       u",".join(fields),
                                                                                       u','.join(
                                                                                           [u'%s'] * len(fields))),
                sql = str(sql[0])
                # 插入数据如果数据重复则更新已有数据
                for f in fields:
                    sql += u'{}=VALUES({}),'.format(f, f)
                sql = sql[:-1] + u';'
                self.cur.execute(sql, values)
                self.conn.commit()
                self.cur.execute(
                    u"UPDATE {} SET update_date='{}' WHERE url='{}';".format(TableName, datetime.datetime.now(),
                                                                             items[u'url']))
                self.conn.commit()
                logging.info(u"数据插入/更新成功!")
            else:
                logging.error(u"未对该爬虫创建数据库表!")
        except MySQLdb.Error, e:
            logging.error(u"Mysql Error %d: %s" % (e.args[0], e.args[1]))

    # 关闭爬虫
    def close_spider(self):
        self.driver.quit()
        self.cur.close()
        self.conn.close()
