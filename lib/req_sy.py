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
    def get_html(self, url, is_json = False, data = None):
        html = ''
        res_code = 200
        try:
            res_code, html = self._get_data_by_requests(url, is_json)
            if res_code == 200:
                # 重置失败重连次数
                self.reconnect_time = 0
                return html
        except Exception as e:
            self._reconnect_after_fail(self.get_html.__name__, url, is_json)

    # Post方式获取html数据
    def post_html(self, url, data, is_json=False):
        data = ''
        res_code = 200
        try:
            res_code, data = self._post_data_by_requests(url, data, is_json=is_json)
            if res_code == 200:
                # 重置失败重连次数
                self.reconnect_time = 0
                return data
        except Exception as e:
            self._reconnect_after_fail(self.post_html.__name__, url, is_json, data=data)

    def test(self, url, type):
        print("调用成功，url:{0}".format(url))


    # 请求失败重连
    def _reconnect_after_fail(self, func_name, url, is_json, data = None):
        data = ''
        allow_reconnect_time = config.CONNECT_TIME
        req_func = getattr(self, func_name)
        if self.reconnect_time < allow_reconnect_time:
            logger.error("# stop {0} seconds, reconnect {1}, method:{2}#".format(allow_reconnect_time, url, func_name))
            time.sleep(allow_reconnect_time)
            self.reconnect_time += 1
            data = req_func(url, is_json, data)
        else:
            logger.error(u"#{0}连接失败，连接次数: {1}, {2}#".format(func_name, self.reconnect_time , url))
            # 重置失败重连次数
            self.reconnect_time = 0
        return data


    # 通过requests包获取HTML页面
    def _get_data_by_requests(self, url, is_json = False):
        timeout = config.TIMEOUT if config.TIMEOUT else 10
        headers = config.HEADERS if config.HEADERS else {}
        headers['user-agent'] = Sy_Request.random_user_agent()
        s = requests.session()
        res = s.get(url, timeout=timeout, allow_redirects=True, headers=headers,cookies={}, verify=False)
        if is_json:
            return res.status_code, res.json()
        else:
            return res.status_code, res.content
    
    # 通过requests包POST方式获取data
    def _post_data_by_requests(self, url, data, is_json=False):
        timeout = config.TIMEOUT if config.TIMEOUT else 10
        headers = config.HEADERS if config.HEADERS else {}
        headers['user-agent'] = Sy_Request.random_user_agent()
        r = requests.post(url, timeout=timeout, data=data, headers=headers)
        if is_json:
            res_code, html = r.status_code, r.json()
        else:
            res_code, html = r.status_code, r.content

        
    # 获取随机User-agent
    @staticmethod
    def random_user_agent():
        return random.choice(config.USER_AGENTS)
        
    

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





def run(url, data):
    req_sy = Sy_Request()
    req_sy.post_html(url, {},  is_json=True)
    req_sy.get_html('htpp://www.google.com')

if __name__ == "__main__":
    run('http://www.google.com.hk', data={})

