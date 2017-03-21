# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json, time, sys, os, re
from hashlib import sha1
from BaseFetcher import BaseFetcher
from lib.log_sy import logger
from lib.orm_sy import Hero
from pprint import pprint 

class HeroFetcher(BaseFetcher):
    def __init__(self):
        super(HeroFetcher, self).__init__('pvpHeros')
        self.hero_js = 'http://pvp.qq.com/web201605/js/herolist.json';
        self.item_js = 'http://pvp.qq.com/web201605/js/item.json';
        self.summoner_js = 'http://pvp.qq.com/web201605/js/summoner.json';
        self.ming_js = 'http://pvp.qq.com/web201605/js/ming.json';
        self.save_path = '/data/wwwroot/shenyou/statics/game/pvp'
        self.hero_length = 64
        self.heros = None

    def getBaseJson(self):
        try:
            heros = self.req.get_html(self.hero_js, is_json=True)
            items = self.req.get_html(self.item_js, is_json=True)
            summoners = self.req.get_html(self.summoner_js, is_json=True)
            mings = self.req.get_html(self.ming_js, is_json=True)
        except Exception as e:
            logger.error('王者荣耀 Base Json Fetche error:' + e)
        self.heros = []
        # 对hero添加topic_id映射
        for hero in heros:
            tmp_hero = hero
            hero_id = 0
            ms_hero = self.session.query(Hero).filter(Hero.ename == tmp_hero['ename']).first()
            if not ms_hero is None:
                hero_id = ms_hero.topicid
            tmp_hero['id'] = hero_id
            self.heros.append(tmp_hero)
            
        # 持久json文件
        self._saveJson(json.dumps(self.heros), 'hero.json')
        self._saveJson(json.dumps(items), 'item.json')
        self._saveJson(json.dumps(summoners), 'summoner.json')
        self._saveJson(json.dumps(mings), 'ming.json')      

    def _saveJson(self, data, filename):
        if(not os.path.exists(self.save_path)):
            os.mkdir(self.save_path)
        with open(os.path.join(self.save_path, filename), 'w') as f:
            f.write(data)

    def processHeros(self):
        if self.heros is None:
            return
        for hero in self.heros:
            time.sleep(2)
            hero_id = hero['ename']
            url = 'http://pvp.qq.com/web201605/herodetail/{0}.shtml'.format(hero_id)
            pprint(url)
            self._processSingleHero(url, hero_id)

    def _processSingleHero(self, url, hero_id):
        hero_res = {}
        html = self.req.get_html(url, is_json=False)
        if html.strip() != '':
            try:
                soup = BeautifulSoup(html, 'html.parser', from_encoding='gbk')
                beijing = soup.find(class_='story-info info').find(class_='nr').p
                hero_res['id'] = hero_id
                #hero_res['desc'] = beijing.text
                skills = soup.find(class_='skill-show').find_all(class_='show-list')
                skill_imgs = soup.find(class_='skill-u1').find_all('li')
                # 组装英雄技能
                skill_arr = []
                for idx, skill in enumerate(skills):
                    tmp = {}
                    tmp['name'] = skill.a.text
                    tmp['p1'] = skill.find(class_='skill-p1').text
                    tmp['p2'] = skill.find(class_='skill-p2').text
                    tmp['p3'] = skill.find(class_='skill-p3').text
                    tmp['img'] = skill_imgs[idx].img['src']
                    skill_arr.append(tmp)
                hero_res['skills'] = skill_arr
                # 组装相关英雄
                rel_hero_arr = []
                rel_hreos = soup.find_all(class_='hero-list hero-relate-list fl')
                for hero in rel_hreos:
                    str_ids = hero['data-relatename']
                    str_new_ids = ''
                    rel_hero_arr.append(str_ids)
                    # 处理英雄映射ID
                    for id in str_ids.split('|'):
                        ms_hero = self.session.query(Hero).filter(Hero.ename == id).first()
                        if not ms_hero is None:
                            str_new_ids += str(ms_hero.topicid)
                            str_new_ids += '|'
                    str_new_ids = str_new_ids[:-1]
                    rel_hero_arr.append(str_new_ids)
                pprint(rel_hero_arr)               

                # 组装出装
                hero_res['rel_heros'] = rel_hero_arr
                equipment_arr = []
                equipments = soup.find_all(class_='equip-list fl')
                for equipment in equipments:
                    equipment_arr.append(equipment['data-item'])
                hero_res['equipments'] = equipment_arr
                # 组装明文
                mings = soup.find(class_='sugg-u1')['data-ming']
                hero_res['mings'] = mings
                # 组装能力
                abilities = soup.find_all(class_='cover-list-bar')
                hero_ability = ''
                for ability in abilities:
                    tmp = str(ability.i['style'])[6:] + '|'
                    hero_ability += tmp
                hero_res['ability'] = hero_ability[:-1]
                # 组装出装
                sug_skills = soup.find_all('img', class_='jn-pic1')
                sug_skills_arr = []
                for sug_skill in sug_skills:
                    sug_skills_arr.append(sug_skill['src'])
                hero_res['sug_skills'] = sug_skills_arr
                # 组装召唤师技能
                hero_zhs_skills = soup.find(id='skill3')['data-skill']
                hero_res['zhs_skills'] = hero_zhs_skills
                # 组装皮肤
                skins = soup.find(class_='pic-pf-list pic-pf-list3')['data-imgname']
                hero_res['skins'] = skins
                hero_json = json.dumps(hero_res)
                self._saveJson(hero_json, '{0}.json'.format(hero_id))                      
            except Exception as e:
                    logger.error('parse Html error:' + e)
    

if __name__ == '__main__':
    # js 缓存时间控制
    hero_fetch = HeroFetcher()
    hero_fetch.getBaseJson();
    if len(hero_fetch.heros) > hero_fetch.hero_length:
        hero_fetch.processHeros()
