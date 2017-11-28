import configparser
import platform

import time

from mylogger import Logger
from robot import Robot
from sms_leave_stone import stoneobject

if __name__ == '__main__':
    # 日志实例化
    logname = "离职节点超时提示.log"
    log = Logger(logname)
    logger = log.getlogger()
    logger.debug("主程序开始运行")
    # 配置文件实例化
    conf = configparser.ConfigParser()
    if platform.system() == 'Windows':
        conf.read("sms_leave.conf", encoding="utf-8-sig")
    else:
        conf.read("sms_leave.conf")
    # sqlite3 数据库连接实例化
    stone = stoneobject()
    # 获取 apikey
    apikey = conf.get(section='apikey', option='key')
    print(apikey)
    robot = Robot(conf=conf, logger=logger, stone=stone, apikey=apikey)
    while True:
        robot.run()
        time.sleep(60*2)
