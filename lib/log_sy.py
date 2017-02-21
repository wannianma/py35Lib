#!/usr/bin/env python
# coding=utf-8

import config
import logging
from logging.handlers import TimedRotatingFileHandler

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
        self.error_info = {
            'ERROR_RECONNECT': {
                'msg': u'重连操作',
                'num': 0
            },
        }

    def setup(self):
        logging.basicConfig(level=self.__log_level)
        # 写入日志文件
        fileTimeHandler = TimedRotatingFileHandler(self.__logfile, "D", 1)
        fileTimeHandler.suffix = "%Y%m%d.log"
        fileTimeHandler.setFormatter(self.__formatter)
        fileTimeHandler.setLevel(self.__log_level)

        # 创建一个handler，输出到控制台
        ch = logging.StreamHandler()
        ch.setFormatter(self.__formatter)
        ch.setLevel(self.__log_level)
        self.__logger.addHandler(fileTimeHandler)
        self.__logger.addHandler(ch)
        self.__logger.propagate = False

    def error(self, msg=None):
        self.__error_num += 1
        self.__logger.error(msg);
        # if not err_type in self.error_info:
        #     return
        # self.error_info[err_type]['num'] += 1
        # if msg is None:
        #     self.__logger.error("**{0}**".format(self.error_info[err_type]['msg']))
        # else:
        #     self.__logger.error("**{0}** #{1}#".format(err_type, msg))

    def info(self, msg):
        self.__info_num += 1
        self.__logger.info(msg)

    def getLogInfo(self):
        return self.__info_num, self.__error_num

logger = Sy_Log()
logger.setup()

if __name__ == "__main__":
    logger.info('one info')
    logger.error('one_error')
    print(logger.getLogInfo())
