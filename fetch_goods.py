#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json, time, sys, os, re
from hashlib import sha1
from lib.orm_sy import Shopping_Goods
from BaseFetcher import BaseFetcher

# 修复插入数据库乱码问题
reload(sys)
sys.setdefaultencoding('utf-8')
 
class GoodsPicDownloader(QiniuFetcher):
    def __init__(self, pre):
        super(GoodsPicDownloader, self).__init__('pic')
        self.key_pre = pre

    def downPicsByQiniu(self):
        keys = self.redis.keys(self.key_pre + '*')
        if len(keys) < 100:
            return
        for key in keys:
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

class GoodsFetcher(BaseFetcher):
    def __init__(self, brand, cat, url):
        super(GoodsFetcher, self).__init__()
        self.brand = brand
        self.goods_cat = cat
        self.start_url = url
    
    def fetchJdGoods(self):
        # 初始page
        start_page = 1
        max_page = 120
        good_count = 0
        error_time = 0
        for page in xrange(start_page, max_page):
            goods_list = []
            # 休息1秒钟
            time.sleep(1)
            list_url = self.start_url + '&page={0}'.format(page)
            logger.info("###########list Url: {0} ###############".format(list_url))
            html = self.req.get_html(list_url, is_json = False)
            if html.strip() != '':
                try:
                    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
                    items = soup.find_all(class_='gl-item')
                    for good in items:
                        good_info = {}
                        good_thumb = good.find(class_='p-img').a.img
                        good_info['name'] = good.find(class_='p-name').a.em.string
                        good_info['link'] = 'http:{0}'.format(good.find(class_='p-img').a['href'])
                        goods_list.append(good_info)                    
                except Exception as e:
                    logger.error('parse Html error: {0}'.format(e))
            else:
                error_time += 1
                logger.error('Failed Get Return Message, error_time:{0}, res:{1}'.format(error_time, html))
                if error_time > 5:
                    break
            # 对当前列表页的商品进行处理
            for good in goods_list:
                good_count += 1
                good_link = good['link']
                good_name = good['name']
                logger.info('good_count: {0}, good_link: {1}'.format(good_count, good_link))
                good_id, good_desc, good_pics, seo_keywords, seo_desc = self.fetchSingleGoodInfo(good_link)
                if good_pics:
                    good_thumb = good_pics[0]
                else:
                    good_thumb = ''
                # 其他信息更新到mysql
                now = int(time.time())
                shopping_good = Shopping_Goods(catid=self.goods_cat, pid=self.brand, title=good_name, content=good_desc, desc=good_link, price = 0, seo_title=good_name, seo_keywords=seo_keywords, seo_desc=seo_desc, thumb=good_thumb, inputtime=now)
                self.session.add(shopping_good)
                self.session.commit()
                # 将轮播图片和price信息存入redis，待下载和更新
                single_key = 'JD_Good_{0}'.format(shopping_good.id)
                self.redis.set(single_key, json.dumps({'thumb':good_thumb, 'pics': good_pics, 'good_id' : good_id}))



    # 获取单一商品信息
    def fetchSingleGoodInfo(self, good_url):
        self.__sleep()
        good_id = ''
        good_desc = ''
        good_pics = {}
        good_price = {}
        html = sel.req.get_html(good_url, is_json = False)
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
                # 获取商品ID
                math
                match_obj = re.search(r'http:(.*)\/(\d+)\.html', str(good_url), re.M|re.I)
                if match_obj:
                    good_id = match_obj.group(2)
                # 获取商品价格（Modify, 上篇价格单独处理
                # good_price = self.fetchGoodPrice(good_url)
            except Exception as e:
                logger.error('parse Html error: {0}'.format(e))
        return good_id, good_desc, good_pics, seo_keyword, seo_desc                
    
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
    
    # sleep 3 seconds
    def __sleep(self):
        time.sleep(1)
        logger.info('#sleep 1 seconds#')
    
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
            except Exception as e:
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
    list_url = 'https://list.jd.com/list.html?cat=670,671,672&ev=exbrand_48100&delivery=0&stock=1&sort=sort_totalsales15_desc&trans=1&JL=2_1_0#J_crumbsBar'
    if store_type == 'jd':
        fetchJD(brand, category, list_url)
    else:
        pass