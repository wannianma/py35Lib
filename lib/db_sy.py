#-*-coding:utf-8-*-
#!/usr/bin/python

#
# DB module 
#

'DB'

import MySQLdb
import config
from logger_sy import logger
import time
import gevent
from gevent.pool import Pool
import os
import random
gpool = Pool(config.GPOOLSIZE)

def getConnection():
    dbconn = MySQLdb.connect(host=config.DB_HOST,user=config.DB_USER,passwd=config.DB_PASSWD,charset=config.DB_CHARSET)
    dbconn.select_db(config.DB_NAME)
    return dbconn 

def db_insert(dbconn, insert_data, tb_type='onlive'):
    # 通过eval动态使用字符串调用函数
    callback_func = eval('_insert_'+tb_type+'_data')
    cursor = dbconn.cursor()
    print "length:%d" % len(insert_data)
    for kw in insert_data:
        gpool.spawn(callback_func, cursor, kw)
    gpool.join()
    cursor.close()
    # 提交修改
    dbconn.commit()

def db_update(dbconn, update_data, onlive_src, is_get_livedata, tb_type='onlive'):
    # 更新之前，先将历史数据的is_live字段置为0
    callback_func = eval('_update_'+tb_type+'_data')
    _before_update_data(dbconn, onlive_src)
    print('Before update!')
    cursor = dbconn.cursor()
    print "lenth:%d" % len(update_data)
    for kw in update_data:
        gpool.spawn(callback_func, cursor, kw, is_get_livedata)
    gpool.join()
    cursor.close()
    # 提交修改
    dbconn.commit()

#cgx
def db_select(dbconn,vid,tb_type='video'):
    callback_func = eval('_select_'+tb_type+'_data')
    cursor = dbconn.cursor()
    res = callback_func(cursor, vid)
    gpool.join()
    cursor.close()
    #提交修噶
    dbconn.commit()
    return res

#查询数据库，看vid是否存在cgx
def _select_video_data(cursor,vid):
    try:
        res = cursor.execute("SELECT * FROM "+config.DB_TABLE_VIDEO_DATA+" WHERE `vid` = %s",vid )
    except Exception as e:
        logger.error("%s | %s" % ('DB Update Error', e))
        raise
    return res





def _update_onlive_data(cursor, kw, is_get_livedata = True):
    try:
        cursor.execute("SELECT * FROM "+config.DB_TABLE+" WHERE `zbid` = %s AND `source` = %s", (kw['zbid'], kw['source']))
        data = cursor.fetchone()
        if data:
            if not is_get_livedata:
                # 主要针对斗鱼平台
                cursor.execute("UPDATE " +config.DB_TABLE+" SET `zbname`=%s, `m_livedata`= %s, `title`=%s, `views`=%s, `isOnlive`=1, `updatetime`=%s, `livedata`=%s, `thumb`= %s, `category`=%s WHERE `zbid` = %s AND `source` = %s", (kw['zbname'], kw['m_livedata'], kw['title'], kw['views'], kw['inputtime'], kw['livedata'], kw['thumb'], kw['category'], kw['zbid'], kw['source']))
            else:
                cursor.execute("UPDATE " +config.DB_TABLE+" SET `zbname`=%s, `m_livedata`= %s, `title`=%s, `views`=%s, `isOnlive`=1, `updatetime`=%s, `avatar`=%s, `thumb`= %s, `category`=%s, `livedata` = %s WHERE `zbid` = %s AND `source` = %s", (kw['zbname'], kw['m_livedata'], kw['title'], kw['views'], kw['inputtime'], kw['zb_thumb'], kw['thumb'], kw['category'], kw['livedata'], kw['zbid'], kw['source']))
        else:
            _insert_onlive_data(cursor, kw)
    except Exception as e:
        logger.error("%s | %s" % ('DB Update Error', e))
        raise

def _before_update_data(dbconn, source):
    cursor = dbconn.cursor()
    try:
        cursor.execute("UPDATE " +config.DB_TABLE+" SET `isOnlive`= 0 WHERE `source` = %s", source)
    except Exception as e:
        logger.error("%s | %s" % ('DB Before Update Error', e))
        raise
    cursor.close()
    dbconn.commit()

#将图片数据存入数据库
def _insert_picture_data(cursor,kw):
    try:
        inputtime = str(int(time.time()))
        thumb = 'http://www.shenyou.tv/uploadfile/'+str(kw['thumb'])
        #thumb = 'http://127.0.0.1/shenyou/uploadfile/'+str(kw['thumb'])

        print "title:" + kw['title']
        n=0
        arr=''
        for url in kw['urls']:
            #arr+=str(n)+" =>\n array(\n 'url'=>'http://127.0.0.1/shenyou/uploadfile/"+str(url)+"',\n 'alt'=>'"+kw['title']+"',\n),\n"
            arr+=str(n)+" =>\n array(\n 'url'=>'http://www.shenyou.tv/uploadfile/"+str(url)+"',\n 'alt'=>'"+kw['title']+"',\n),\n"
            n=n+1
        pic_data = "array ("+arr+" \n)"

        #将爬取到的图集粗如数据库，分类为38(网游壁纸)，并设置状态为1级审核
        cursor.execute("INSERT INTO " +config.DB_TABLE_PICTURE+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES ('38', '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['title'], thumb, kw['keywords'], kw['description'], inputtime, inputtime))
        insert_id = cursor.lastrowid
        # 更新url
        url = "http://www.shenyou.tv/gallary/" + str(insert_id)+".html"
        cursor.execute("UPDATE "+config.DB_TABLE_PICTURE+" SET `url` = %s WHERE `id` = %s", (url, str(insert_id)))

        #更新hits表
        cursor.execute("INSERT INTO sy_hits (`hitsid`, `catid`) VALUES ('c-3-%s', '38')",insert_id)
        #将图集具体数组写入数据库
        cursor.execute("INSERT INTO "+config.DB_TABLE_PICTURE_DATA+" (`id`, `content`, `readpoint`, `groupids_view`, `paginationtype`, `maxcharperpage`, `template`, `paytype`, `allow_comment`, `relation`, `pictureurls`,`copyfrom`) VALUES (%s, '', 0, '', 0, 0, '', 0, '1', '', %s, '|0')", (str(insert_id),pic_data))
        #向控制台输入已经插入数据库的id
        print "insert_id :" + str(insert_id)


    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise


def _insert_video_data(cursor,kw):
    try:
	v_views = random.randint(200,500)
        #####
        inputtime = str(int(time.time()))
        print "title:" + kw['title']
        #将爬取到的视频，存入其他(14)分类，并设置状态为1级审核
        cursor.execute("INSERT INTO " +config.DB_TABLE_VIDEO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`,`vision`,`video_category`,`anchor`) VALUES ('14', '0', %s, '', %s, %s, %s, '0', '', '0', '1', '1', '0', 'admin', %s, %s,'1','1',%s)",(kw['title'], kw['pic'], kw['keywords'], kw['description'], inputtime, inputtime,kw['anchor']))
        insert_id = cursor.lastrowid

        # 更新url
        url = "http://www.shenyou.tv/video/" + str(insert_id)+".html"
        cursor.execute("UPDATE "+config.DB_TABLE_VIDEO+" SET `url` = %s WHERE `id` = %s", (url, str(insert_id)))

        #更新hits表
        cursor.execute("INSERT INTO sy_hits (`hitsid`, `catid`,`views`, `updatetime`) VALUES ('c-11-%s', '14',%s, %s)" % (insert_id, v_views, inputtime))
        #将vid写入data附表
        cursor.execute("INSERT INTO "+config.DB_TABLE_VIDEO_DATA+" (`id`, `content`, `readpoint`, `groupids_view`, `paginationtype`, `maxcharperpage`, `template`, `paytype`, `allow_comment`, `relation`, `video`, `from`, `vid`, `videoTime`) VALUES (%s, '', 0, '', 0, 10000, '', 0, '1', '', '1', %s, %s, %s)", (str(insert_id), kw['from'], kw['vid'], kw['videoTime']))

        # #将vid与from写入vdata目录的json中

        dir_name = str(insert_id % 100)
        path = "/data/wwwroot/ShenYou/vdata/"+dir_name
        if(os.path.exists(path)!=True):
            os.mkdir(path)
	json_str = '{"from":"%s","vid":"%s"}' % (kw['from'] , kw['vid'])
        f=file(path+"/"+str(insert_id)+".json","w+")
        f.write(str(json_str))
        f.close()
        #向控制台输入已经插入数据库的id
        print "insert_id :" + str(insert_id)

    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise




def _insert_toutiao_data(cursor, kw):
    try:
	sql = "SELECT * FROM {0} WHERE `title` = '{1}'".format(config.DB_TABLE_TOUTIAO_DIF, kw['title'])
        res = cursor.execute(sql)
    except Exception as e:
        logger.error("%s | %s" % ('DB Select Error', e))
        raise
    if not res :
        insert_sql = "insert into `{0}` (`title`) values ('{1}')".format(config.DB_TABLE_TOUTIAO_DIF, kw['title'])
  	cursor.execute(insert_sql)

        #判断内容长度是否大于94个字符
        cont_len = len(kw['content'])
	#n_views = random.randint(200,500)
        if cont_len > 550:
            try:
                inputtime = str(int(time.time()))
                title = kw['title']
                #判断catid是否等于34(其他)----如果等于34则根据标题判断文章所属分类
    	        if kw['catid']==34:
                    if title.find('lol')>=0:
                        cursor.execute("INSERT INTO " +config.DB_TABLE_TOUTIAO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES ('28', '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['title'], kw['pic'], kw['keywords'], kw['description'],inputtime, inputtime))
                    elif title.find('dota')>=0:
                        cursor.execute("INSERT INTO " +config.DB_TABLE_TOUTIAO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES ('30', '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['title'], kw['pic'], kw['keywords'], kw['description'],inputtime, inputtime))
                    #当标题含有‘星际’关键字
                    elif title.find('\u661f\u9645')>=0:
                        cursor.execute("INSERT INTO " +config.DB_TABLE_TOUTIAO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES ('35', '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['title'], kw['pic'], kw['keywords'], kw['description'], inputtime, inputtime))
                    #当标题含有‘炉石’关键字
                    elif title.find('\u7089\u77f3'):
                        cursor.execute("INSERT INTO " +config.DB_TABLE_TOUTIAO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES ('36', '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['title'], kw['pic'], kw['keywords'], kw['description'],inputtime, inputtime))
                else:
                    cursor.execute("INSERT INTO " +config.DB_TABLE_TOUTIAO+" (`catid`, `typeid`, `title`, `style`, `thumb`, `keywords`, `description`, `posids`, `url`, `listorder`, `status`, `sysadd`, `islink`, `username`, `inputtime`, `updatetime`) VALUES (%s, '0', %s, '', %s, %s, %s, '0', '', '0', '99', '1', '0', 'admin', %s, %s)",(kw['catid'],kw['title'], kw['pic'], kw['keywords'], kw['description'],inputtime, inputtime))

                insert_id = cursor.lastrowid
                # 更新url
                url = "http://www.shenyou.tv/article/" + str(insert_id)+".html"
                #更新hits表
		cursor.execute("INSERT INTO sy_hits (`hitsid`, `catid`, `views`, `updatetime`) VALUES ('c-1-%s', %s, '0', %s)",(insert_id, kw['catid'], inputtime))
                cursor.execute("UPDATE "+config.DB_TABLE_TOUTIAO+" SET `url` = %s WHERE `id` = %s", (url, str(insert_id)))
                # 将content插入到data附表
                cursor.execute("INSERT INTO "+config.DB_TABLE_TOUTIAO_DATA+" (`id`, `content`, `readpoint`, `groupids_view`, `paginationtype`, `maxcharperpage`, `template`, `paytype`, `relation`, `voteid`, `allow_comment`, `copyfrom`, `from`) VALUES (%s, %s, 0, '', 0, 10000, '', 0, '', 0, 1, '|0', %s)", (str(insert_id), kw['content'], kw['n_from']))
		#更新搜索表search
                cursor.execute("INSERT INTO "+"sy_search"+" (`typeid`, `id`, `adddate`, `data`, `siteid`) VALUES (1, %s, %s, %s, 1)", (str(insert_id), inputtime, kw['title']+': '+kw['n_search']))

                print "insert_id :" + str(insert_id)
            except Exception as e:
                logger.error("%s | %s" % ('DB Insert Error', e))
                raise

def _insert_onlive_data(cursor, kw):
    try:
        cursor.execute("INSERT INTO " +config.DB_TABLE+" (`zbid`, `zbname`, `source`, `title`, `views`, `category`, `isOnlive`, `inputtime`, `avatar`, `thumb`, `livedata`, `catid`, `typeid`, `status`, `m_livedata`) VALUES (%s, %s, %s, %s, %s, %s, '1', %s, %s, %s, %s, 9, 8, 99,%s)",(kw['zbid'],kw['zbname'],kw['source'],kw['title'],kw['views'],kw['category'],kw['inputtime'],kw['zb_thumb'],kw['thumb'],kw['livedata'],kw['m_livedata']))
    except Exception as e:
        logger.error("%s | %s" % ('DB Insert Error', e))
        raise

def run():
    pass

if __name__ == "__main__":
    run()
