# -*- coding: utf-8 -*-
# @Time : 2023/11/18 22:55
# @Author : DanYang
# @File : data_loader.py
# @Software : PyCharm
from pathlib import Path
from typing import Union

import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt

from logger import Logger


def butter_filter(data, kwargs):
    N = kwargs.get("N", 10)
    Wn = kwargs.get("Wn", 0.1)
    btype = kwargs.get("btype", "low")

    b, a = butter(N, Wn, btype)
    filtered_data = filtfilt(b, a, data)

    return filtered_data


def inertial_filter(data, kwargs):
    a = kwargs.get("a", 0.03)
    y_data = data.copy()
    for pos, y in enumerate(y_data):
        if pos == 0:
            continue
        else:
            y_data[pos] = a * data[pos] + (1 - a) * y_data[pos - 1]

    return y_data


def load_data(file_path: Union[Path, str], encoding: str) -> pd.DataFrame:
    try:
        df = pd.read_table(file_path, delimiter=",", encoding=encoding)
        df.columns = [i.strip() for i in df.columns]
        Logger.info(f"读取文件:{file_path}\n{df.head()}")
        return df
    except Exception as e:
        Logger.error(f"读取文件{file_path}失败")
        raise e


def preprocess_data(w0: float, file_path: Union[Path, str], old_columns: tuple[str, ...] = ("时间", "温度", "热重"),
                    new_columns: tuple[str, ...] = ("T", "TG", "TG/W", "DTG", "FDTG"), index_name: str = "t",
                    filter_method="inertial", **kwargs) -> pd.DataFrame:
    drop_first = kwargs.get("drop_first", False)
    encoding = kwargs.get("encoding", "GB2312")
    if filter_method == "butter":
        filter_tool = butter_filter
    else:
        filter_tool = inertial_filter

    df = load_data(file_path, encoding=encoding)
    TG = df[old_columns[-1]]
    df[new_columns[-3]] = TG / w0

    df.drop(0, axis=0, inplace=True)
    DTG = np.diff(TG) / w0
    df[new_columns[-2]] = DTG
    df[new_columns[-1]] = np.diff(filter_tool(TG, kwargs)) / w0

    df.drop(old_columns[0], axis=1, inplace=True)
    df.index.name = index_name

    df.columns = new_columns
    if drop_first:
        df.drop(1, axis=0, inplace=True)

    Logger.info(f"处理数据:\n{df.head()}")
    return df


if __name__ == '__main__':
    df = preprocess_data(9.4, "data/ymt.txt")
    print(df)

