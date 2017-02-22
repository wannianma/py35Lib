# coding=utf-8
from sqlalchemy import create_engine, Column, Integer, String, Sequence, Text, Index, SmallInteger, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_URI
from log_sy import logger
import atexit

# 创建对象的基类:
Base_Model = declarative_base()

class User(Base_Model):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_seq'),
                primary_key=True, autoincrement=True)
    name = Column(String(50))


## 战队表
class Team(Base_Model):
    __tablename__ = 'sy_team'

    topicid = Column(Integer, primary_key=True)
    title = Column(String(128))
    sName = Column(String(20))
    url = Column(String(128))
    country = Column(String(20))
    description = Column(Text)
    keywords = Column(String(255))
    thumb = Column(String(255))
    support_num = Column(Integer)
    inputtime = Column(Integer)
    updatetime = Column(Integer)


## 赛事表
class Season(Base_Model):
    __tablename__ = 'sy_season'

    topicid = Column(Integer, primary_key=True)
    title = Column(String(128))
    description = Column(Text)
    keywords = Column(String(255))
    thumb = Column(String(255))
    inputtime = Column(Integer)
    updatetime = Column(Integer)


class Match(Base_Model):
    __tablename__ = 'sy_match'

    id = Column(Integer, primary_key=True, autoincrement=True)
    catid = Column(SmallInteger)
    typeid = Column(SmallInteger)
    title = Column(String(80))
    style = Column(String(24), default='')
    thumb = Column(String(100), default='')
    keywords = Column(String(40))
    description = Column(String(255))
    posids = Column(SmallInteger, default=0)
    url = Column(String(100), default='')
    listorder = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    sysadd = Column(SmallInteger, default=0)
    username = Column(String(20))
    inputtime = Column(Integer)
    updatetime = Column(Integer, default=0)
    match_type = Column(String(50))
    match_status = Column(String(50))
    match_start_time = Column(Integer)
    match_end_time = Column(Integer)
    live_url = Column(String(255))
    __table_args__ = (Index('status_idx', 'status', 'listorder', 'id'),
                      Index('listorder_idx', 'catid', 'status', 'listorder', 'id'),
                      Index('catid_idx', 'catid', 'status', 'id'))


class Match_Data(Base_Model):
    __tablename__ = 'sy_match_data'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    paginationtype = Column(SmallInteger, default=0)
    maxcharperpage = Column(SmallInteger, default=0)
    template = Column(String(30), default='')
    allow_comment = Column(Integer, default=1)
    relation_video = Column(String(255))
    topics = Column(String(50))
    team = Column(String(50))
    relation_article = Column(String(255), default='')


class Match_Team(Base_Model):
    __tablename__ = 'sy_match_team'
    __table_args__ = (Index('id_idx', 'id', 'matchid', 'teamid'),)

    id = Column(Integer, primary_key=True)
    matchid = Column(Integer)
    teamid = Column(Integer)
    result = Column(SmallInteger)
    up_num = Column(Integer)
    inputtime = Column(Integer)

class Video(Base_Model):
    __tablename__ = 'sy_video'

    id = Column(Integer, primary_key=True, autoincrement=True)
    catid = Column(SmallInteger)
    typeid = Column(SmallInteger)
    title = Column(String(200))
    style = Column(String(24))
    thumb = Column(String(100))
    keywords = Column(String(80))
    description = Column(String(255))
    posids = Column(SmallInteger)
    url = Column(String(100))
    listorder = Column(SmallInteger)
    status = Column(SmallInteger, default=1)
    sysadd = Column(SmallInteger, default=1)
    islink = Column(SmallInteger, default=0)
    username = Column(String(20), default='spider')
    inputtime = Column(Integer)
    updatetime = Column(Integer)
    vision = Column(String(255))
    video_category = Column(String(255))
    anchor = Column(Integer)
    istop = Column(SmallInteger, default=0)

class Video_Data(Base_Model):
    __tablename__ = 'sy_video_data'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    readpoint = Column(SmallInteger, default=0)
    groupids_view = Column(SmallInteger, default=0)
    paginationtype = Column(SmallInteger, default=0)
    maxcharperpage = Column(SmallInteger, default=0)
    template = Column(String(30), default='')
    paytype = Column(SmallInteger, default=0)
    allow_comment = Column(Integer, default=1)
    relation = Column(String(255), default='')
    video = Column(SmallInteger, default=0)
    # 关键字重复特殊处理
    from_ = Column('from', String(20))
    vid = Column(String(255))
    videoTime = Column(String(255))
    topics = Column(String(50))
    sy_vkey = Column(String(255))

class Hits(Base_Model):
    __tablename__ = 'sy_hits'

    hitsid= Column(String(30), primary_key=True)
    catid = Column(SmallInteger, default=0)
    views = Column(Integer, default=0)
    yesterdayviews = Column(Integer, default=0)
    dayviews = Column(Integer, default=0)
    weekviews = Column(Integer, default=0)
    monthviews = Column(Integer, default=0)
    updatetime = Column(Integer, default=0)

class Search(Base_Model):
    __tablename__ = 'sy_search'

    searchid = Column(Integer, primary_key=True, autoincrement=True)
    typeid = Column(SmallInteger)
    id = Column(Integer)
    adddate = Column(Integer)
    data = Column(Text)
    siteid = Column(SmallInteger, default=1)

# Topic表
class Topic(Base_Model):
    __tablename__ = 'sy_topic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128))
    content_count = Column(Integer, default=0)
    focus_count = Column(Integer, default=0)
    description = Column(Text)
    keywords = Column(String(255))
    pic = Column(String(255))
    thumb = Column(String(255))
    lock = Column(SmallInteger, default=0)
    user_created = Column(SmallInteger, default=0)
    seo_title = Column(String(255))
    parentid = Column(Integer, default=0)
    is_parent = Column(SmallInteger, default=0)
    is_recommend = Column(SmallInteger, default=0)
    status = Column(SmallInteger, default=0)
    # 默认类型为战队
    type = Column(SmallInteger, default=3)
    omnipotent = Column(Text, default='')
    content_count_last_week = Column(Integer, default=0)
    content_count_last_month = Column(Integer, default=0)
    inputtime = Column(Integer, default=0)
    updatetime = Column(Integer, default=0)
    aliasname = Column(String(128))
    es_name = Column(String(50))

# Topic_Relation表
class Topic_Relation(Base_Model):
    __tablename__ = 'sy_topic_relation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer)
    content_id = Column(Integer)
    model_id = Column(Integer)
    inputtime = Column(Integer)

# Shopping_Goods表
class Shopping_Goods(Base_Model):
    __tablename__ = 'sy_shopping_goods'

    id = Column(Integer, primary_key=True, autoincrement=True)
    catid = Column(Integer)
    pid = Column(Integer)
    title = Column(String(255))
    desc = Column(Text, default='')
    content = Column(Text, default='')
    seo_title = Column(String(255), default='')
    seo_keywords = Column(String(255), default='')
    seo_desc = Column(String(255), default='')
    thumb = Column(String(255))
    pics = Column(Text, default='')
    price = Column(DECIMAL, default=0)
    support_num = Column(Integer, default=0)
    focus_num = Column(Integer, default=0)
    inputtime = Column(Integer)
    updatetime = Column(Integer, default=0)
    views = Column(String(50))
    status = Column(SmallInteger, default=99)
    

class Sy_Session(object):
    __session = None

    # 数据库创建
    @staticmethod
    def init_db():
        Base_Model.metadata.create_all(bind=eng)
    
    # 数据库销毁
    @staticmethod
    def drop_db():
        Base_Model.metadata.drop_all(bind=eng)
    
    # 获取数据库连接
    @staticmethod
    def get_session():
        if Sy_Session.__session is None:
            eng = create_engine(DB_URI)
            Base_Model = declarative_base()
            DB_session = sessionmaker(bind=eng)
            ## 生成数据库连接实例
            Sy_Session.__session = DB_session()
            atexit.register(Sy_Session.del_session)
        
        return Sy_Session.__session

    # 销毁数据库连接
    @staticmethod
    def del_session():
        try:
            Sy_Session.__session.commit()
        except Exception as e:
            logger.error('Session Commit in del_session, info : {0}'.format(e))
        finally:
            Sy_Session.__session.close()
            logger.info('session close succes')

def get_result():
    session = Sy_Session.get_session()
    goods = session.query(Shopping_Goods)
    for good in goods:
        print(good.title)

if __name__ == '__main__':
    get_result()
