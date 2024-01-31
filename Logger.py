# -*- coding: utf-8 -*-
# @Time : 2024/1/28 20:40
# @Author : DanYang
# @File : Logger.py
# @Software : PyCharm
import logging


def setup_logger(name, log_file='Log.log', level=logging.INFO):
    """
    设置一个可以将日志输出到文件和控制台的logger
    :param name: logger的名称
    :param log_file: log文件地址
    :param level: log级别
    :return: logger
    """
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger