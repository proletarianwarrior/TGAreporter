# -*- coding: utf-8 -*-
# @Time : 2024/1/28 19:51
# @Author : DanYang
# @File : DataLoader.py
# @Software : PyCharm
import os
import re
import time
from pathlib import Path
from configparser import ConfigParser

import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt

from Logger import setup_logger

logger = setup_logger('load_data')
cfg = ConfigParser()
cfg.read('./config.ini', encoding='utf-8')


def _reset():
    cfg.set('DataProcess', 'method', 'user_define')
    cfg.set('DataProcess', 'weight', 'user_define')
    cfg.set('DataPlot', 'coal_pyrolysis', '100,150')
    cfg.set('DataPlot', 'carbon_combustion', '300,350')
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        cfg.write(configfile)


def _butter_filter(data: np.ndarray, **kwargs):
    N = kwargs.get('N', cfg.getint('DataProcess', 'N'))
    Wn = kwargs.get('Wn', cfg.getfloat('DataProcess', 'Wn'))
    btype = cfg.get('DataProcess', 'btype')
    alpha = kwargs.get('alpha', cfg.getfloat('DataProcess', 'alpha'))
    b, a = butter(N=N, Wn=Wn, btype=btype)
    filtered_data = filtfilt(b, a, data)
    filtered_data = pd.Series(filtered_data).ewm(alpha=alpha).mean().values

    return filtered_data


def _inertial_filter(data, **kwargs):
    a = kwargs.get('a', cfg.getfloat('DataProcess', 'a'))
    y_data = data.copy()
    for pos, y in enumerate(y_data):
        if pos == 0:
            continue
        else:
            y_data[pos] = a * data[pos] + (1 - a) * y_data[pos - 1]

    return y_data


def _load_data(file_path: Path) -> pd.DataFrame:
    o_file_path = cfg.get('DataLoading', 'file_path')
    if os.path.abspath(o_file_path) != os.path.abspath(file_path):
        logger.warning(f'路径初始化或发生改变!{o_file_path}->{file_path}')
        _reset()
        cfg.set('DataLoading', 'file_path', str(file_path))
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            cfg.write(configfile)
    delimiter = cfg.get('DataLoading', 'delimiter')
    encoding = cfg.get('DataLoading', 'encoding')
    try:
        df = pd.read_table(file_path, delimiter=delimiter, encoding=encoding, dtype=float)
        df.columns = [i.strip() for i in df.columns]
        if (columns_list := ','.join(list(df.columns))) != (
        default_columns_list := cfg.get('DataLoading', 'default_columns')):
            logger.warning(
                f'\n文件表头与系统默认不符,请检查文件是否正确!\nuser: {columns_list}\ndefault: {default_columns_list}')
        logger.info(f'读取文件{file_path.name}成功！\n{df.head(n=3)}')
        return df
    except Exception as e:
        raise e


def _process_data(file_path: Path) -> pd.DataFrame:
    df = _load_data(file_path)
    time.sleep(0.2)
    weight = cfg.get('DataProcess', 'weight')
    sep_time = cfg.getfloat('DataProcess', 'sep_time')
    drop_first = cfg.getboolean('DataProcess', 'drop_first')

    while not bool(re.match(r'^[-+]?\d+[.]?\d*$', weight)):
        weight = input('请输入煤粉试样的质量: ')
        if not bool(re.match(r'^[-+]?\d+[.]?\d*$', weight)):
            logger.error(f'请输入正确的质量!({weight}不可以表示质量)')
            time.sleep(0.2)
    cfg.set('DataProcess', 'weight', weight)
    new_columns = cfg.get('DataProcess', 'new_columns').split(',')

    method = cfg.get('DataProcess', 'method')
    while method not in ['butter', 'inertial']:
        method = int(input('选择滤波器类型(输入序号):\n1.butter\t2.inertial\n'))
        if method == 1:
            method = 'butter'
        elif method == 2:
            method = 'inertial'
        cfg.set('DataProcess', 'method', method)
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        cfg.write(configfile)

    TG = df['热重']
    DTG = np.diff(TG) / sep_time / float(weight)
    if method.lower() == 'butter':
        n_TG = _butter_filter(TG)
    elif method.lower() == 'inertial':
        n_TG = _inertial_filter(TG)
    else:
        logger.error(f'没有{method}这一滤波器种类,请从butter,inertial中选择!')
        raise NameError('滤波器名称错误!')
    n_DTG = np.diff(n_TG) / sep_time / float(weight)
    if drop_first:
        df.drop(0, inplace=True)
    else:
        DTG = np.hstack((DTG[0], DTG))
        n_DTG = np.hstack((n_DTG[0], n_DTG))
    df[new_columns[0]] = DTG
    df[new_columns[1]] = n_DTG

    with open('config.ini', 'w', encoding='utf-8') as configfile:
        cfg.write(configfile)

    logger.info(f'预处理数据成功!\n{df.head(n=3)}')
    return df


if __name__ == '__main__':
    _reset()
    path = Path('./data/ymt.txt')
    df = _process_data(path)
