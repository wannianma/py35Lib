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
    
class GoodsPicDownloader(QiniuFetcher):
    def __init__(self, pre):
        super(GoodsPicDownloader, self).__init__('pic')
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

class GoodsFetcher(QiniuFetcher):
    def __init__(self, brand, cat, url):
        super(GoodsFetcher, self).__init__('pic')
        self.brand = brand
        self.goods_cat = cat
        self.start_url = url
    
    def fetchJdGoods(self):
        # 初始page
        start_page = 1
        max_page = 120
        good_count = 0
        for page in xrange(start_page, max_page):
            logger.info("###########page {0} ###############".format(page))
            goods_list = []
            # 休息1秒钟
            time.sleep(1)
            list_url = self.start_url + '&page={0}'.format(page)
            logger.info("###########list Url: {0} ###############".format(list_url))
            html = get_html(list_url, is_json = False)
            if html.strip() != '':
                try:
                    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                    items = soup.find_all(class_='gl-item')
                    pprint(len(items))
                    for good in items:
                        good_info = {}
                        good_thumb = good.find(class_='p-img').a.img
                        # matchObj = re.search( r'data-lazy-img=\"(.*.jpg)\"', str(good_thumb), re.M|re.I)
                        # if matchObj:
                        #     good_thumb = matchObj.group(1)
                        # else:
                        #     good_thumb = good_thumb['src']
                        good_info['name'] = good.find(class_='p-name').a.em.string
                        # good_info['thumb'] = 'http:{0}'.format(good_thumb)
                        good_info['link'] = 'http:{0}'.format(good.find(class_='p-img').a['href'])
                        goods_list.append(good_info)                    
                except Exception, e:
                    logger.error('parse Html error: {0}'.format(e))

            else:
                error_time += 1
                logger.error('Failed Get Return Message, error_time:{0}, res:{1}'.format(error_time, html))
                if error_time > 10:
                    break
            for good in goods_list:
                good_count += 1
                good_link = good['link']
                good_name = good['name']
                logger.info('good_count: {0}, good_link: {1}'.format(good_count, good_link))
                good_desc, good_pics, good_price, seo_keywords, seo_desc = self.fetchSingleGoodInfo(good_link)
                if good_pics:
                    good_thumb = good_pics[0]
                else:
                    good_thumb = ''
                # 取值
                good_price = good_price['p'] if good_price else 0 
                # 将轮播图片存入redis，待下载
                single_key = 'jdGood_{0}'.format(good_link)
                self.redis.set(single_key, json.dumps({'thumb':good_thumb, 'pics': good_pics}))
                # 其他信息更新到mysql
                now = int(time.time())
                shopping_good = Shopping_Goods(catid=self.goods_cat, pid=self.brand, title=good_name, content=good_desc, desc=good_link, price = good_price, seo_title=good_name, seo_keywords=seo_keywords, seo_desc=seo_desc, thumb=good_thumb, inputtime=now)
                session.add(shopping_good)
            session.commit()
            
    def fetchSingleGoodInfo(self, good_url):
        self.__sleep()
        good_desc = ''
        good_pics = {}
        good_price = {}
        html = get_html(good_url, is_json = False)
        if html.strip() != '':
            try:
                soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                # 获取keywords
                good_keyword = soup.find('meta', attrs={'name':'keywords'})
                seo_keyword = good_keyword['content']
                # 获取description
                good_desc = soup.find('meta', attrs={'name':'description'})
                seo_desc = good_keyword['content']
                # 获取商品列表图
                lis = soup.find(id='spec-list').find_all('li')
                good_pics = []
                for li in lis:
                    img_src = li.img['src']
                    # 替换为高分辨图片
                    img_src = img_src.replace('s54x54_jfs', 's450x450_jfs')
                    img_src = img_src.replace('n5/jfs', 'n1/jfs')
                    good_pics.append('http:{0}'.format(img_src))
                # 获取商品描述
                good_desc = str(soup.find(class_='parameter2 p-parameter-list'))
                pprint(good_pics)
                # 获取商品价格
                good_price = self.fetchGoodPrice(good_url)
            except Exception, e:
                logger.error('parse Html error: {0}'.format(e))
        return good_desc, good_pics, good_price, seo_keyword, seo_desc                
    
    def fetchGoodPrice(self, url):
        ## api_addr = get_html(url, is_js=True)
        self.__sleep()
        price_data = {}
        match_obj = re.search(r'http:(.*)\/(\d+)\.html', str(url), re.M|re.I)
        if match_obj:
            api_addr = 'http://p.3.cn/prices/mgets?callback=jQuery56582&type=1&area=1&pdtk=&pduid=1487580141768936841430&pdpin=&pdbp=0&skuIds=J_{0}'.format(match_obj.group(2))
        else:
            return price_data
        # 去除\n空字符
        jsonp_data = get_html(api_addr)
        if jsonp_data.strip() != '':
            matchObj = re.search( r'jQuery\d+\(\[(.*)\]\);\s', str(jsonp_data), re.M|re.I)
            if matchObj:
                price_data = json.loads(matchObj.group(1))
        pprint(price_data)                 
        return price_data
        
    def fetchPicInfo(self, tag):
        # 初始page
        start_page = 1
        max_page = 500
        error_time = 0
    
    # sleep 3 seconds
    def __sleep(self):
        time.sleep(3)
        logger.info('#sleep 3 seconds#')
    
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
  
def fetchJD(brand, category, url):
    good_fetch = GoodsFetcher(brand, category, url)
    good_fetch.fetchJdGoods()
    # good_fetch.fetchSingleGoodInfo('http://item.jd.com/3742530.html')
    # good_fetch.fetchGoodPrice('http://item.jd.com/3243688.html')
    

if __name__ == '__main__':
    store_type = sys.argv[1]
    brand = '3'
    category = '198'
    list_url = 'https://list.jd.com/list.html?cat=670,671,672&ev=exbrand_11516&delivery=0&stock=1&sort=sort_totalsales15_desc&trans=1&JL=2_1_0#J_crumbsBar'
    if store_type == 'jd':
        fetchJD(brand, category, list_url)
    else:
        pass