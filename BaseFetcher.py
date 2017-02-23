#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

from qiniu import Auth
from qiniu import BucketManager
from lib.config import ACCESS_KEY, SECRET_KEY, BUCKET, BUCKET_PRE
from bs4 import BeautifulSoup
import redis, json, time, sys, os, re
from hashlib import sha1
from lib.log_sy import logger
from lib.req_sy import Sy_Request
from lib.orm_sy import Sy_Session
from pprint import pprint

# 修复插入数据库乱码问题
reload(sys)
sys.setdefaultencoding('utf-8')

# decorator
def used_time(fn):
    def wrapper(*args, **kwargs):
        start = int(time.time())
        res = fn(*args, **kwargs)
        end = int(time.time())
        logger.info("Used Time: {0} Seconds".format((end-start)))
        return res
    return wrapper

class BaseFetcher(object):
    ## Class Attribute
    name = 'Base'

    def __init__(self):
        ## private variable begin with '__'
        # qiniu配置初始化
        self.bucket_name = BUCKET
        self.upload_pre = BUCKET_PRE
        self.__auth = Auth(ACCESS_KEY, SECRET_KEY)
        self.__bucket = BucketManager(self.__auth)
        # redis连接
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        # 数据库orm连接
        self.session = Sy_Session.get_session()
        self.req = Sy_Request()

    @used_time
    def qiniu_fetch_file(self, url, key):
        try:
            ret, info = self.__bucket.fetch(url, self.bucket_name, key)
            pprint(info)
            if ret and str(ret['key']) == key:
                return True
            else:
                return False
        except Exception as e:
            logger.error("qiniu远程fetch文件出错，info:{0}".format(e))
            return False

    # 生成video的唯一key值
    def generate_video_key(self, videoid):
        timeArray = time.localtime(time.time())
        key = '{0}/{1}'.format(timeArray.tm_mday, timeArray.tm_mon)
        token1 = str(hex(timeArray.tm_hour + timeArray.tm_min + timeArray.tm_sec + int(videoid)))[2:]
        token2 = sha1(os.urandom(24) + self.type).hexdigest()[0:16]
        return key + '/{0}-{1}-{2}.mp4'.format(token1, videoid, token2)

    # 生成图片的唯一key值
    # date : 2016-09-18
    def generate_pic_key(self, type):
        pass

    

def test():
    fetcher = BaseFetcher()
    # fetcher.qiniu_fetch_file('http://a.zdmimg.com/201702/16/58a5b259ab4996135.jpg_f710.jpg', 'test/new_img.jpg')
    pprint(fetcher.req.get_html('http://www.shihuo.cn/sports/getDropdown'))

if __name__ == "__main__":
    test()