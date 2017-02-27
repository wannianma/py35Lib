#-*-coding:utf-8-*-
#!/usr/bin/python3.5

# Email config
EMAIL_FROM = '###'
EMAIL_PASSWORD = '###'
EMAIL_TO = '###'
EMAIL_SMTP_SERVER = 'smtp.qq.com'
EMAIL_CHARSET = 'utf-8'
EMAIL_PORT = 25
EMAIL_MAX_SIZE = 60

#logger config
LOG_NAME = 'crawler'
LOG_FILENAME = 'jd_goods_crawler.log'
BASIC_LOG_PATH = '/home/wyh/src/Code/python/sy-shells/log/'

#mysql config
DB_HOST = '###'
DB_USER = 'shenyou'
DB_PASSWD = '###'
DB_CHARSET = 'utf8'
DB_NAME = 'test_shenyou'
DB_URI = 'mysql://{}:{}@{}/{}?charset={}'.format(
    DB_USER, DB_PASSWD, DB_HOST, DB_NAME, DB_CHARSET)

#gevent and requests config
GPOOLSIZE = 10
TIMEOUT = 5
HEADERS = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
    'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
    'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
]
CONNECT_TIME = 3

#worker config
INTERVAL = 1

#Token key
SERVER_KEY = 'SY@20151017'

#Qiniu config
BUCKET = 'shenyou'
BUCKET_PRE = 'uploads/'
ACCESS_KEY = '###'
SECRET_KEY = '###'
