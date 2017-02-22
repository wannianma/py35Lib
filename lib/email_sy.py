#-*-coding:utf-8-*-
#!/usr/bin/python3.5

#
# Send Email with Content Log
#

'Send Log By Email'

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from datetime import datetime
from queue_sy import Sy_Queue
from log_sy import logger
import smtplib, json, time, atexit
import config


class Sy_Email(object):
    ## Class Attribute, 类变量
    name = 'Email'

    def __init__(self):
        ## private variable begin with '__'
        self.__email_queue = Sy_Queue()
        self.__from_addr = config.EMAIL_FROM
        self.__to_addr = config.EMAIL_TO
        self.__charset = config.EMAIL_CHARSET
        # 设置发送服务器    
        self.__server = smtplib.SMTP(config.EMAIL_SMTP_SERVER, config.EMAIL_PORT)
        try:
            self.__server.set_debuglevel(0)
            self.__server.login(self.__from_addr, config.EMAIL_PASSWORD)
        except Exception as e:
            logger.error("EMAIL SERVER INIT FAIL, info:{0}".format(e))
            self.__server = None
        finally:
            # 注册自动释放连接函数
            atexit.register(self.destroy)

    def destroy(self):
        logger.info("SMTP Server close!")
        self.__server.quit()

    # 发送email方法
    def send_email(self, subject, content, to_addr=None, content_type='plain'):
        to_addr = to_addr if to_addr else self.__to_addr
        msg = MIMEText(content, content_type, self.__charset)
        msg['From'] = self._format_addr('ShenYou.TV<{0}>'.format(self.__from_addr))
        msg['To'] = self._format_addr('管理员<{0}>'.format(to_addr))
        msg['subject'] = Header(subject, self.__charset).encode()

        if not self.__server is None:
            self.__server.sendmail(self.__from_addr, [self.__to_addr], msg.as_string())
            logger.info("send email success, from:{0}, to:{1}".format(self.__from_addr, self.__to_addr))

    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    
    # push到邮件发送队列
    def push_email(self, subject, content, to_addr=None):
        to_addr = to_addr if to_addr else self.__to_addr
        self.__email_queue.lpush('{"to_addr":"%s", "subject":"%s", "content":"%s"}'% (to_addr, subject, content))
    
    # 批量发送邮件
    def send_emails(self):
        emails = self.__email_queue.getjobs()
        for em in emails:
            obj = json.loads(em)
            subject = obj['subject']
            content= obj['content']
            address = obj['to_addr']
            self.send_email(subject, content, to_addr = address)
            # 防止不间断发送邮件遭拒收
            time.sleep(2)

def run():
    email = Sy_Email()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S');
    for i in range(1):
        email.push_email('测试发送邮件模块', '当前时间' + current_time)
    email.send_emails()


if __name__ == "__main__":
    run()
