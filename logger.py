# -*- coding: utf-8 -*-
# @Time : 2023/11/18 23:07
# @Author : DanYang
# @File : logger.py
# @Software : PyCharm
import logging
import os


def setup_logger(name, log_file, level=logging.INFO):
    """设置一个可以将日志输出到文件和控制台的logger"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # 创建一个handler来写入日志文件
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # 创建一个handler来打印日志
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # 创建一个logger并添加handler
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


Logger = setup_logger("reporter_logger", "reporter.log")
