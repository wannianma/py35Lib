# -*- coding: utf-8 -*-

## 本脚本用于更新赛事比赛数据以及相关的比赛视频、比赛比分等

from lib.orm_sy import session, Video_Data, Team, Topic, Topic_Relation, Video, Match_Data, Match, Match_Team, Search, Hits, init_db, drop_db
from lib import req_sy
from pprint import pprint
from bs4 import BeautifulSoup
import json, time, re

def get_json(file_name, name_pre = './data'):
    file_name = name_pre + '/' + file_name
    res = None
    with open(file_name, 'r') as f:
        res = json.loads(f.read())
    return res


## 获取当前数据对应战队，战队不存在，则添加
def get_team(arr_team, now):
    pprint(arr_team['sname'])
    team = session.query(Team).filter(Team.sName == arr_team['sname']).first()
    if team is None:
        topic = Topic(title=arr_team['title'], description=arr_team['title'], keywords=arr_team['sname'], thumb=arr_team['thumb'], seo_title=arr_team['sname']+u"战队",
                      is_parent=0, parentid=6, status=1, type=2, aliasname=arr_team['sname'], es_name=arr_team['sname'], inputtime=now)
        session.add(topic)
        session.commit()
        team = Team(topicid = topic.id, title=arr_team['title'], sName=arr_team['sname'], thumb=arr_team['thumb'], url=arr_team['link'], support_num=5,
                    country=arr_team['countries']['name'], inputtime=now)
        session.add(team)
        # commit and get team.id
        session.commit()
    return team

## 抓取match页面，获取relation_video和game_type|result
def get_match_detail(match):
    time.sleep(2)
    now = int(time.time())
    html = req_sy.get_html(match['link'], is_json=False)
    if html.strip() != '':
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        match_type = soup.find(class_='bl-wt').text
        bifen_cls = soup.find(class_='bf')
        team_a_result = bifen_cls.find(class_='l').text
        team_b_result = bifen_cls.find(class_='r').text
        print('Match Type:{0}, result:{1}-{2}'.format(match_type, team_a_result, team_b_result))
        videos = soup.find(class_='matchvideCon').find_all(class_='videoshow')
        relation_video = '|'
        for index, video in enumerate(videos):
            vid = video['flash']
            vid = vid[vid.find('vid=')+4:vid.find('&')]
            title = match['title']+u'第'+str(index+1)+u'场'
            video_obj = Video(title=title, keywords=title, description=title, inputtime=match['etime'], anchor=2144, catid=119, status=99, typeid=0, style='', thumb='', posids=0, url='',listorder=0, updatetime=0, vision=0, video_category=0)
            session.add(video_obj)
            session.commit()
            # 更新video的url字段
            session.query(Video).filter(Video.id == video_obj.id).update({Video.url:'http://www.shenyou.tv/video/{0}.html'.format(video_obj.id)})
            video_data_obj = Video_Data(id = video_obj.id, content=title, vid= vid, topics='6', from_='tengxun')
            session.add(video_data_obj)
            # 更新topic_relation表
            topic_relation = Topic_Relation(topic_id= 6, content_id=video_obj.id, model_id=11, inputtime=match['etime'])
            session.add(topic_relation)
            # 更新Search表
            seach_obj = Search(typeid=57, id=video_obj.id, adddate=now, data=title)
            session.add(seach_obj)
            # 更新Hits表
            hits_obj = Hits(hitsid='c-11-{0}'.format(video_obj.id), catid=119)
            session.add(hits_obj)
            session.commit()
            relation_video = relation_video + str(video_obj.id) + '|'
    return match_type, team_a_result, team_b_result, relation_video[1:len(relation_video)-1]

def run_shell():
    now = int(time.time())
    data = get_json('2016MSI.json')
    season_id = 37258
    season_thumb = 'http://static.shenyou.tv/uploadfile/2016/1128/20161128060358329.jpg'
    # print '*' * 20 + "Drop DB"
    # drop_db()
    # print '*' * 20 + "Init DB"
    # init_db()
    print '*' * 20 + "Update Data"
    for val in data['list']:
        match_type, team_a_result, team_b_result, relation_video = get_match_detail(val)
        match = Match(catid=117, typeid=0, title=val['title'], keywords=val['title'], description=val['title'], thumb=season_thumb, sysadd=1,
                      inputtime=now, username='spider', status=99, match_type=match_type, live_url=val['link'], match_start_time=val['stime'], match_end_time=val['etime'], match_status=2)
        session.add(match)
        # commit and get match.id
        session.commit()
        team_a = get_team(val['ateam'], now)
        team_b = get_team(val['bteam'], now)
        relation_topics = '6'+'|'+str(season_id)+'|'+str(team_a.topicid)+'|'+str(team_b.topicid)
        # update match topic_relation
        for topic_id in re.split('\|', relation_topics):
            topic_relation = Topic_Relation(topic_id=topic_id, content_id=match.id, model_id=19, inputtime=match.match_end_time)
            session.add(topic_relation)

        # update match video topic_relation (avoid video duplatied)
        video_datas = session.query(Video_Data).filter(Video_Data.id.in_([int(x) for x in re.split('\|', relation_video)])).all()
        for video_data in video_datas:
            video_data.topics = relation_topics
        session.commit()
        for topic_id in re.split('\|', relation_topics):
            for video_id in re.split('\|', relation_video):
                if video_id != '6' or video_id != 6:
                    topic_relation = Topic_Relation(topic_id=topic_id, content_id=video_id, model_id=11, inputtime=match.match_end_time)
                    session.add(topic_relation)
        # get relation_video AND Match_type
        match_d = Match_Data(id=match.id, content=val['title'], topics=relation_topics,
                             team=str(team_a.topicid) + '|' + str(team_b.topicid), relation_video=relation_video)
        session.add(match_d)
        match_team_a = Match_Team(matchid=match.id, teamid=team_a.topicid, result=team_a_result, up_num=1, inputtime=now)
        match_team_b = Match_Team(matchid=match.id, teamid=team_b.topicid, result=team_b_result, up_num=1, inputtime=now)
        session.add(match_team_a)
        session.add(match_team_b)
        session.commit()

    session.commit()

def update_topic_relation():
    matchs = session.query(Match_Data.topics, Match.id, Match.match_end_time).join(Match, Match.id == Match_Data.id).filter(Match_Data.id < 87).all()
    for match in matchs:
        for topic_id in re.split('\|', match.topics):
            topic_relation = Topic_Relation(topic_id=topic_id, content_id=match.id, model_id=19,
                                            inputtime=match.match_end_time)
            pprint(topic_id)
            session.add(topic_relation)
    session.commit()

if __name__ == '__main__':
    update_topic_relation()