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
import json
import MySQLdb
import MySQLdb.cursors
import logging


def load_configs():
    with open("restapi_config.json", "rb")as f:
        txt = f.read()
    txt = json.loads(txt)
    return txt


def mysql_spider(name_spider):
    conf = load_configs()['mysql']
    try:
        conn = MySQLdb.connect(host=conf.get("host", "localhost"), port=conf.get("port", 3306),
                               user=conf.get("user", "root"), passwd=conf.get("passwd", "root"),
                               db=conf.get("db"), charset=u"utf8", cursorclass=MySQLdb.cursors.DictCursor)
        cur = conn.cursor()
        cur.execute(u"SELECT * FROM net_spider WHERE spider_name='{}'".format(name_spider))
        try:
            keywords = cur.fetchall()[0]
        except:
            print u"爬虫名:{}".format(name_spider)
            cur.close()
            conn.close()
            raise logging.error(u"爬虫名:{} 配置信息未找到!".format(name_spider))
    except MySQLdb.Error, e:
        cur.close()
        conn.close()
        raise logging.error(u"Mysql Error %d: %s" % (e.args[0], e.args[1]))

    cur.close()
    conn.close()
    return keywords
