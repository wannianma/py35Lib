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


class PicFetcher(QiniuFetcher):
    def __init__(self, url):
        super(PicFetcher, self).__init__('pic')
        self.start_url = url

    def fetchPicInfo(self, tag):
        # 初始page
        start_page = 1
        max_page = 500
        error_time = 0
        for page in xrange(start_page, max_page):
            # 休息1秒钟
            time.sleep(1)
            res = post_html(self.start_url, {'page':page, 'type':u'时间', 'tag':tag}, is_json=True)
            if res and len(res) > 0:
                # error_time 重新置0
                error_time = 0
                for link in res:
                    link_url = link['url']
                    single_key = 'pic_' + link_url
                    logger.info(link_url)
                    if not self.checkPicExist(single_key):
                        link['origin_pics'] = self.getOriginPicAddr(link_url)
                        link['tag'] = tag
                        self.redis.set(single_key, json.dumps(link))
                    else:
                        logger.error('pic is already existed, key: {0}'.format(single_key))
            else:
                error_time += 1
                logger.error('Failed Get Return Message, error_time:{0}, res:{1}'.format(error_time, res))
                if error_time > 10:
                    break

    def checkPicExist(self, key):
        return self.redis.exists(key) or self.redis.exists('old_' + key)
    
    # 从图片单页获取原始图片地址
    def getOriginPicAddr(self, link):
        time.sleep(0.5)
        origin_pic_address = []
        html = get_html(link, is_json=False)
        if html.strip() != '':
            try:
                soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                pics = soup.find(class_='picmidmid').find_all('li')
                for pic in pics:
                    pic_url = pic.a.img['bigimg']
                    origin_pic_address.append(pic_url)
            except Exception, e:
                logger.error('parse Html error:' + e)
        
        return origin_pic_address    

class PicDownloader(QiniuFetcher):
    def __init__(self, pre):
        super(PicDownloader, self).__init__('pic')
        self.key_pre = pre

    def downPicsByQiniu(self):
        keys = self.redis.keys(self.key_pre + '*')
        if len(keys) < 100:
            return
        for key in keys:
            print key
            pic_info = json.loads(self.redis.get(key))
            pic_remote_urls = pic_info['origin_pics']
            new_pic_urls = []
            pub_date = pic_info['pubdate']
            for pic_url in pic_remote_urls:
                new_key = self.generate_pic_key(pub_date)
                logger.info('new_pic_url: {0}{1}'.format('http://static.shenyou.tv/', new_key))
                new_pic_urls.append('{0}{1}'.format('http://static.shenyou.tv/', new_key))
                self.fetch_file(pic_url, new_key)
            # 更新key值信息
            pic_info['is_process'] = 1
            pic_info['origin_pics'] = new_pic_urls
            self.redis.delete(key)
            self.redis.set(key.replace('pic_', 'old_pic_'), json.dumps(pic_info))
  
def fetchPics():
    pic_fetch = PicFetcher('http://www.wangye.cn/plus/imageajax_new.php')
    pic_fetch.fetchPicInfo(u'巨乳')
    pic_fetch.fetchPicInfo(u'黑丝')
    pic_fetch.fetchPicInfo(u'制服')
    pic_fetch.fetchPicInfo(u'古典')
    pic_fetch.fetchPicInfo(u'萝莉')
    pic_fetch.fetchPicInfo(u'名人')
    pic_fetch.fetchPicInfo(u'女优')
    

def downPics():
    PicFetcher = PicDownloader('pic_')
    STOP_TIME = 120
    start = 0
    while start < 120:
        logger.info('5 Seconds Pass, new Round')
        PicFetcher.downPicsByQiniu()
        time.sleep(5)
        start += 1
    

if __name__ == '__main__':
    cmd_type = 'fetch' if len(sys.argv) == 1 else sys.argv[1]
    if cmd_type == 'fetch':
        fetchPics()
    else:
        downPics()