#-*-coding:utf-8-*-
#!/usr/bin/python3.5

#
# Send Email with Content Log
#

'GET HTML CONTENT'

import config
import subprocess
import requests
from log_sy import logger
import logging
import random
import hashlib
from pprint import pprint

# for delete
import json,time

# disable Requests log messages
logging.getLogger("requests").setLevel(logging.WARNING)

class Sy_Request(object):
    ## Class Attribute
    name = 'Request'

    def __init__(self):
        # 抓取失败重连次数
        self.reconnect_time = 0
    
    # Get方式获取数据
    def get_html(self, url, type=None):
        html = ''
        res_code = 200
        try:
            res_code, html = self._fetch_data_by_requests(url)
            if res_code == 200:
                return html
        except Exception as e:
            pass

    def test(self, url, type):
        pprint(url, type)


    # 请求失败重连
    def reconnect_after_fail(self, func_name, func_args):
        func = getattr(self, func_name)
        func(func_args)

#     # 通过requests包获取HTML页面
#     def _fetch_data_by_requests(self, url, is_json = False):
#         timeout = config.TIMEOUT if config.TIMEOUT else 10
#         headers = config.HEADERS if config.HEADERS else {}
#         headers['user-agent'] = Sy_Request.random_user_agent()
#         s = requests.session()
#         res = s.get(url, timeout=timeout, allow_redirects=True, headers=headers,cookies={}, verify=False)
#         if is_json:
#             return res.status_code, res.json()
#         else:
#             return res.status_code, res.content
        
#     # 获取随机User-agent
#     @staticmethod
#     def random_user_agent():
#         return random.choice(config.USER_AGENTS)
        
    
# def get_html(url, is_json=False, is_js=False, connect_time=0):

#     except Exception, e:
#         reconnect_time = config.CONNECT_TIME
#         if (connect_time < reconnect_time):
#             # 暂停五秒
#             logger.error("# stop {0} seconds, get reconnect {1}#".format(str(reconnect_time), url))
#             time.sleep(reconnect_time)
#             connect_time = connect_time + 1
#             html = get_html(url, is_json, is_js, connect_time)
#         else:
#             logger.error(u"#get连接次数: {0}, {1}#".format(str(reconnect_time), url))
#             return ''

#     return html


# # 执行phantomjs获取网页内容
# def _fetch_api_addr_by_phantomjs(url):
#     cmd = '/home/wyh/bin/phantomjs /home/wyh/src/Code/python/sy-shells/js/pro_jd.js %s' % url
#     try:
#         logger.info('cmd:{0}'.format(cmd))
#         stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
#         # print 'err:', stderr
#     except Exception, e:
#         logger.error(stderr)
#     return 200, stdout


# def post_html(url, data, is_json=False, connect_time=0):
#     html = ''
#     res_code = 200
#     try:
#         headers = config.HEADERS
#         headers["user-agent"] = random_user_agent()
#         r = requests.post(url, data=data, headers=headers)
#         if is_json:
#             res_code, html = r.status_code, r.json()
#         else:
#             res_code, html = r.status_code, r.content
#         if res_code == 200:
#             return html
#     except Exception, e:
#         logger.error("%s | %s" % (e, url))

# def post_json(url, data, is_json=True):
#     try:
#         r = requests.session().post(url, json=data)
#         if is_json:
#             res_code, html = r.status_code, r.json()
#         else:
#             res_code, html = r.status_code, r.content
#         if res_code == 200:
#             return html
#     except Exception, e:
#         logger.error("%s | %s" % (e, url))


# def random_user_agent():
#     return random.choice(config.USER_AGENTS)


# # 通过requests包获取HTML页面
# def _fetch_html_by_requests(url, is_json=False, allow_redirects=True, timeout=None, headers={}, cookies={}, proxy={},
#                             stream=False, verify=False, user_agent=None, **kw):
#     timeout = timeout or config.TIMEOUT
#     headers = headers or config.HEADERS
#     headers["user-agent"] = user_agent or random_user_agent()
#     s = requests.Session()
#     r = s.get(url, timeout=timeout, allow_redirects=allow_redirects, headers=headers, cookies=cookies,
#                   stream=stream, verify=verify)
#     if is_json:
#         return r.status_code, r.json()

#     return r.status_code, r.content


def run(url, type):
    req_sy = Sy_Request()
    pprint(locals())
    req_sy.reconnect_after_fail(req_sy.test.__name__, locals())

if __name__ == "__main__":
    import time
    sha1 = hashlib.sha1()
    sha1.update(str(time.time())[0:7])
    sha1.update('SY@20151017')
    token = sha1.hexdigest()
    print 'http://api.shenyou.tv/admin.php?m=Admin&c=Spider&a=anchors&token=' + token
    run('http://api.shenyou.tv/admin.php?m=Admin&c=Spider&a=anchors&token=' + token, '2')
