#-*-coding:utf-8-*-
#!/usr/bin/python3.5

from . import config
import logging
from logging.handlers import RotatingFileHandler

class Sy_Log(object):
    ## Class Attribute
    name = 'Log'

    def __init__(self):
        ## private variable begin with '__'
        self.__log_name = config.LOG_NAME
        self.__logfile = "{0}/{1}".format(config.BASIC_LOG_PATH, config.LOG_FILENAME)
        self.__formatter = logging.Formatter('%(asctime)s # %(filename)s # %(levelname)s - %(message)s')
        self.__log_level = logging.INFO
        self.__logger = logging.getLogger(self.__log_name)
        self.__error_num = 0
        self.__info_num = 0
        self.num = 0
        self.error_info = {
            'ERROR_RECONNECT': {
                'msg': u'重连操作',
                'num': 0
            },
        }

    def setup(self):
        logging.basicConfig(level=self.__log_level)
        # 写入日志文件
        # 根据日志文件大小自行分割 5M
        fileHandler = RotatingFileHandler(self.__logfile, 'a', 5*1024*1024, 10)
        fileHandler.setFormatter(self.__formatter)
        fileHandler.setLevel(self.__log_level)

        # 创建一个handler，输出到控制台
        ch = logging.StreamHandler()
        ch.setFormatter(self.__formatter)
        ch.setLevel(self.__log_level)
        self.__logger.addHandler(fileHandler)
        self.__logger.addHandler(ch)
        self.__logger.propagate = False

    def error(self, msg=None):
        self.__error_num += 1
        self.__logger.error(msg);

    def info(self, msg):
        self.__info_num += 1
        self.__logger.info(msg)

    def getLogInfo(self):
        return self.__info_num, self.__error_num

logger = Sy_Log()
logger.setup()

if __name__ == "__main__":
    for i in range(1,10000):
        logger.info('one info')
