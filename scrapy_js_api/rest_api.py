# -*- coding: utf-8 -*-
# ! /usr/bin/env python

"""
@author:LiWei
@license:LiWei
@contact:877129310@qq.com
@version:V1.0
@var:基于selenumi做javascript渲染爬虫api接口
@note:

"""

from twisted.internet import reactor
from twisted.web import server
from txrestapi.resource import APIResource
from txrestapi.methods import GET
import Queue, json
from utils.middlewares import load_configs, mysql_spider
from spiders.Selenium_Spider import Selenium_Spider
import logging
from logging.handlers import RotatingFileHandler

# 日志级别设置
logging.basicConfig(level=logging.DEBUG,
                    format=u'%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt=u'%Y-%m-%d %H:%M',
                    filename=u'spider_server.log',
                    filemode=u'w')

# 将屏幕打印日志信息
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter(u'用户:%(name)-6s 日志级别: %(levelname)-8s 任务消息:%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# 日志备份
Rthandler = RotatingFileHandler(u'spider_server.log', maxBytes=50 * 1024 * 1024, backupCount=5)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter(u'用户:%(name)-6s 日志级别: %(levelname)-8s 任务消息:%(message)s')
Rthandler.setFormatter(formatter)
logging.getLogger('').addHandler(Rthandler)


class WebSpiderJsApi(APIResource):
    def __init__(self):
        APIResource.__init__(self)
        self.q = Queue.Queue()
        self.conf = load_configs()
        worker1 = Selenium_Spider(self.q)
        worker2 = Selenium_Spider(self.q)
        worker3 = Selenium_Spider(self.q)
        worker1.start()
        worker2.start()
        worker3.start()

    @GET("/schedule")
    def get_schedule(self, request):
        name_spider = request.args['name_spider'][0]
        mysql_spider(name_spider)
        spider_jobid = request.args['spider_jobid'][0]
        project = request.args['project'][0]
        spider_type = request.args['spider_type'][0]
        webdriver = request.args["webdriver"][0]
        try:
            debug = request.args['debug'][0]
        except:
            debug = "False"
        self.q.put({"name_spider": name_spider, "spider_jobid": spider_jobid,
                    "project ": project, "spider_type": spider_type,
                    "webdriver": webdriver, "debug": debug},
                   block=True, timeout=None)  # 产生任务消息

        return json.dumps({"status": "ok", "name_spider": name_spider,
                           "spider_jobid": spider_jobid, "project ": project,
                           "spider_type": spider_type, "debug": debug, "webdriver": webdriver})


# 启动
if __name__ == "__main__":
    site = server.Site(WebSpiderJsApi())
    reactor.listenTCP(6801, site)
    reactor.run()
