#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json, time, sys, os, re
from hashlib import sha1
from lib.orm_sy import Shopping_Goods
from BaseFetcher import BaseFetcher
from lib.log_sy import logger
from pprint import pprint 

class GoodsFetcher(BaseFetcher):
    def __init__(self, brand, cat, url):
        super(GoodsFetcher, self).__init__('good')
        self.brand = brand
        self.goods_cat = cat
        self.start_url = url
        self.redis_list = 'JD_Goods'
        # 已完成处理的list
        self.redis_list_done = 'JD_Goods_Done'
    
    def fetchJdGoods(self):
        # 初始page
        start_page = 1
        max_page = 2
        good_count = 0
        error_time = 0
        for page in range(start_page, max_page):
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
                self.redis.lpush(self.redis_list, json.dumps({good_id : {'thumb':good_thumb, 'pics': good_pics, 'id' : shopping_good.id}}))

    # 获取单一商品信息
    def fetchSingleGoodInfo(self, good_url):
        self.__sleep()
        good_id = ''
        good_desc = ''
        good_pics = {}
        good_price = {}
        html = self.req.get_html(good_url, is_json = False)
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
                    img_src = img_src.replace('s75x75_jfs', 's450x450_jfs')
                    img_src = img_src.replace('n5/jfs', 'n1/jfs')
                    good_pics.append('http:{0}'.format(img_src))
                # 获取商品描述
                good_desc = str(soup.find(class_='parameter2 p-parameter-list'))
                # 获取商品ID
                match_obj = re.search(r'http:(.*)\/(\d+)\.html', str(good_url), re.M|re.I)
                if match_obj:
                    good_id = match_obj.group(2)
                # 获取商品价格（Modify, 上篇价格单独处理
                # good_price = self.fetchGoodPrice(good_url)
            except Exception as e:
                logger.error('parse Html error: {0}'.format(e))
        return good_id, good_desc, good_pics, seo_keyword, seo_desc                
    
    
    def fetchGoodPrice(self, ids):
        ## api_addr = get_html(url, is_js=True)
        price_data = None
        self.__sleep()
        # To J_11134879180%2C
        ids_str = ''.join(['J_{0}%2C'.format(x) for x in ids])[0:-3]
        api_addr = 'https://p.3.cn/prices/mgets?callback=jQuery2719335&type=1&area=1_72_4137_0&skuIds={0}'.format(ids_str)
        logger.info('# api_addr: {0}#'.format(api_addr))
        # 去除\n空字符
        jsonp_data = self.req.get_html(api_addr)
        if jsonp_data.strip() != '':
            matchObj = re.search( r'jQuery\d+', str(jsonp_data), re.M|re.I)
            if matchObj:
                pos1, pos2 = matchObj.span()
                # json decode
                price_data = json.loads(jsonp_data[pos2-1:-3].decode())
        return price_data
    
    # sleep 1 seconds
    def __sleep(self):
        time.sleep(1)
        logger.info('#sleep 1 seconds#')
    
    def updateGoodsExtraInfo(self):
        # 分片获取元素
        start = 0
        end = 0
        num_of_one_round = 15
        list_length = self.redis.llen(self.redis_list)
        while end < list_length:
            end += num_of_one_round
            goods = self.redis.lrange(self.redis_list, start, end)
            jd_ids = []
            goods_dict = {}
            for good in goods:
                good = json.loads(good.decode())
                goods_dict.update(good)
            # 下载good图片信息            
            for key, good in goods_dict.items():
                good['pics'] = self.downloadJdPic(good['pics'])
                good['thumb'] = good['pics'][0]
                jd_ids.append(key)
            # 批量获取价格信息
            prices = self.fetchGoodPrice(jd_ids)
            for price in prices:
                pprint(price)
                good_id = price['id'][2:]
                goods_dict[good_id]['price'] = price
                # 添加已处理信息
                goods_dict[good_id]['processed'] = 1
            # 从list pop当前goods
            for good in goods_dict.values():
                self.redis.lpush(self.redis_list_done, json.dumps(good))
            # 删除已读取list列表
            # self.redis.ltrim(self.redis_list, end+1, -1)
            # 更新start
            start = end
    
    def downloadJdPic(self, data):
        new_pics = []
        for pic_url in data:
            new_key = self.generate_pic_key()
            self.qiniu_fetch_file(pic_url, new_key)
            logger.info('new_pic_url: {0}{1}'.format('http://static.shenyou.tv/', new_key))
            new_pics.append('{0}{1}'.format('http://static.shenyou.tv/', new_key))
        return new_pics

  
def fetchJD(brand, category, url, process_step = 'fetch'):
    good_fetch = GoodsFetcher(brand, category, url)
    if process_step == 'fetch':
        good_fetch.fetchJdGoods()
    else:
        good_fetch.updateGoodsExtraInfo()
    
# 四个参数
# 1 方法类型，fetch | process
# 2 商品列表地址， url
# 3 商品分类，category
# 4 品牌名称， 
if __name__ == '__main__':
    if len(sys.argv) != 5:
        logger.error('参数输入有误')
    process_step = sys.argv[1]
    url = sys.argv[2]
    brand = sys.argv[3]
    category = sys.argv[4]
    fetchJD(brand, category, url, process_step)