#!/usr/bin/python
# -*- coding: utf-8 -*-

from qiniu import Auth
from qiniu import BucketManager
from lib.config import ACCESS_KEY, SECRET_KEY, BUCKET, BUCKET_PRE
from lib.logger_sy import logger
from lib.req_sy import post_html, get_html
from bs4 import BeautifulSoup
import redis, json, time, sys, os
from pprint import pprint
from hashlib import sha1
from lib.orm_sy import session, Shopping_Goods
import re

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

# commit update
def after_update(fn):
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)
        session.commit()
    return wrapper

class QiniuFetcher(object):
    ## Class Attribute
    name = 'Qiniu'

    def __init__(self, type):
        ## private variable begin with '__'
        self.bucket_name = BUCKET
        self.upload_pre = BUCKET_PRE
        self.__auth = Auth(ACCESS_KEY, SECRET_KEY)
        self.__bucket = BucketManager(self.__auth)
        self.type = type
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    @used_time
    def fetch_file(self, url, key):
        try:
            ret, info = self.__bucket.fetch(url, self.bucket_name, key)
            if ret and str(ret['key']) == key:
                return True
            else:
                return False
        except Exception, e:
            logger.info(e)
            return False

    # 生成video的唯一key值
    def generate_key(self, videoid):
        timeArray = time.localtime(time.time())
        key = '{0}/{1}'.format(timeArray.tm_mday, timeArray.tm_mon)
        token1 = str(hex(timeArray.tm_hour + timeArray.tm_min + timeArray.tm_sec + int(videoid)))[2:]
        token2 = sha1(os.urandom(24) + self.type).hexdigest()[0:16]
        return key + '/{0}-{1}-{2}.mp4'.format(token1, videoid, token2)

    # 生成图片的唯一key值
    # date : 2016-09-18
    def generate_pic_key(self, date):
        # 对发布日期进行修改:
        # 2016-09-18 -> 160918
        new_date_key = date[2:].replace('-','')
        token = sha1(os.urandom(24) + self.type).hexdigest()[0:16]
        return self.upload_pre +  new_date_key + '/{0}.jpg'.format(token)

    def get_videos_data(self, limit):
        return session.query(Video_Data).filter(and_(Video_Data.from_ == self.type, Video_Data.sy_vkey == '')).order_by(Video_Data.id.asc()).limit(limit).all()

    def fetch_video_remote_url(self, vid):
        pass

    @after_update
    def update_video_data(self, id, key):
        return session.query(Video_Data).filter(Video_Data.id == id).update({Video_Data.sy_vkey:key})

    def update_videos_data(self):
        pass