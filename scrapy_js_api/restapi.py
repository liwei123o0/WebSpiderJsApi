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
import falcon
from wsgiref import simple_server
from selenium import webdriver
import json


class ApiTest(object):
    def __init__(self):
        self.driver = selenimu_spider()

    def on_get(self, req, resp):
        url = req.get_param("url")
        urlxpath = req.get_param("urlxpath")
        geturl = self.driver.get_url(url, urlxpath)
        resp.data = json.dumps({"url": geturl})
        resp.status = falcon.HTTP_200


class selenimu_spider(object):
    def get_url(self, url, urlxpath):
        geturls = []
        driver = webdriver.PhantomJS()
        driver.get(url)
        urls = driver.find_elements_by_xpath(urlxpath)
        for url in urls:
            geturls.append(url.get_attribute("href"))
        driver.quit()
        return geturls


if __name__ == '__main__':
    spider = ApiTest()
    api = application = falcon.API()
    api.add_route('/spider', spider)
    httpd = simple_server.make_server('127.0.0.1', 8000, api)
    httpd.serve_forever()
