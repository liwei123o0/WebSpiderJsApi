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
import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import logging


class SeleniumSspider(object):
    def __init__(self):
        self.idx = 1
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        # 图片加载超时设置
        self.driver.set_page_load_timeout(30)
        # 脚本加载超时设置
        self.driver.set_script_timeout(30)

    def get_urls(self):
        urls = []
        d1 = datetime.datetime.now()
        # 几天前的时间
        d2 = d1 - datetime.timedelta(days=3)
        day = datetime.datetime.strftime(d1, "%Y:%m:%d")
        today = datetime.datetime.strftime(d2, "%Y:%m:%d")

        url = "http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index={page_index}&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=0&dbselect=bidx&kw=&start_time={day}&end_time={today}&timeType=1&displayZone=%E8%B4%B5%E5%B7%9E%E7%9C%81&zoneId=52&pppStatus=0&agentName="

        for page_index in xrange(1, 10, 1):
            urls.append(url.format(page_index=page_index, day=day, today=today))
        return urls

    def spiders(self):

        urllist = self.get_urls()

        for uri in urllist:
            urls = []
            try:
                self.driver.get(uri)
            except TimeoutException, e:
                logging.error(e)
                continue
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='vT-srch-result-list-bid']/li/a")))
            except TimeoutException, e:
                logging.error(e)
                continue
            urilist = self.driver.find_elements_by_xpath("//ul[@class='vT-srch-result-list-bid']/li/a")
            for urii in urilist:
                urls.append(urii.get_attribute("href"))

            for url in urls:
                try:
                    self.driver.get(url)
                except TimeoutException, e:
                    logging.error(e)
                    continue
                try:
                    self.fields_item()
                except NoSuchElementException, e:
                    logging.error(e)
                    continue

    def fields_item(self):
        pass
        content = self.driver.find_element_by_xpath("//div[@class='table']").text
        print type(content)


if __name__ == "__main__":
    SeleniumSspider().spiders()
