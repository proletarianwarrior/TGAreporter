# -*- coding: utf-8 -*-
# @Time : 2023/11/18 22:56
# @Author : DanYang
# @File : data_parser.py.py
# @Software : PyCharm
import json
import os

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

from logger import Logger


def find_typical_minima(data, n, kwargs):
    tolerance = kwargs.get("tolerance", 1)
    min_down = kwargs.get("min_down", 10)
    data = np.array(data)
    # 反转数据以查找最小值
    inverted_data = -1 * data

    # 找到所有局部最大值的索引（实际上是最小值）
    peaks, _ = find_peaks(inverted_data)

    def count_trend_points(index, direction):
        """计算连续趋势点的个数"""
        count = 0
        tolerance_count = 0
        current = index

        while 0 <= current < len(data) - 1:
            if data[current + direction] - data[current] > 0:
                count += 1
                current += direction
                tolerance_count = 0
            elif tolerance_count < tolerance:
                tolerance_count += 1
                current += direction
            else:
                break

        return count

    # 评估每个最小值的典型性
    typicality_scores = []
    c_peaks = []
    for peak in peaks:
        left_count = count_trend_points(peak, -1)
        right_count = count_trend_points(peak, 1)
        if left_count < min_down or right_count < min_down:
            continue
        c_peaks.append(peak)
        score = left_count + right_count
        typicality_scores.append(score)

    # 找到得分最高的n个最小值的索引
    most_typical_indices = np.argsort(typicality_scores)[-n:]

    # 返回结果：横坐标（索引）和纵坐标（实际最小值）
    return [c_peaks[i] for i in most_typical_indices]


def find_first_stable_point(data, kwargs):
    """
    找出在给定窗口大小内变化低于阈值的第一个数据点。

    :param del_size: 允许的离群个数
    :param data: 数据点列表（一维）。
    :param window_size: 稳定性检查要考虑的点数。
    :param threshold: 将数据视为稳定数据的最大允许变化量。
    :return: 第一个稳定点的索引，如果没有找到稳定点，则为 "None"。
    """
    window_size = kwargs.get("window_size", 500)
    threshold = kwargs.get("threshold", 1e-5)
    del_size = kwargs.get("del_size", 50)
    data = np.array(data)
    n = len(data)
    for i in range(n - window_size):
        max_diff = np.array([abs(data[i] - data[j]) for j in range(i + 1, i + window_size)])
        if sum(max_diff > threshold) < del_size:
            return i
    return None


def get_chara_point(df: pd.DataFrame, x1: float = 1 / 4, x2: float = 1 / 3, x12: float = 3 / 4, recal=False, block=True, **kwargs):
    if os.path.exists("./chara_points.json") and not recal:
        with open("./chara_points.json", "r") as file:
            return json.load(file)
    elif recal:
        Logger.warning("确定更新特征点吗(保存的数据将消失)")
        r = input("Y(y)/N(n)")
        if r.upper() == "Y":
            os.remove("./chara_points.json")
        else:
            get_chara_point(df, x1, x2, x12, recal=False)

    FDTG = df["FDTG"]
    index_min = df.index[0]
    index_max = df.index[-1]
    x1_sep = int(x1 * index_max)
    x2_sep = int(x2 * index_max)

    min_x1 = FDTG[:x1_sep].argmin() + index_min
    min_x2 = FDTG[x2_sep:].argmin() + index_min + x2_sep
    x12_sep = int((min_x2 - min_x1) * x12 + min_x1)
    min_x3 = find_typical_minima(FDTG[x12_sep:min_x2], 1, kwargs)[0] + index_min + x12_sep

    max_x1 = FDTG[:min_x1].argmax() + index_min
    max_x2 = find_first_stable_point(FDTG[min_x1:min_x3], kwargs) + min_x1 + index_min
    max_x3 = (min_x2 - min_x1) - find_first_stable_point(FDTG[min_x2:min_x1:-1], kwargs) + min_x1 + index_min
    max_x4 = FDTG[min_x3:min_x2].argmax() + min_x3 + index_min
    max_x5 = find_first_stable_point(FDTG[min_x2:], kwargs) + min_x2 + index_min

    result = {"min": [int(min_x1), int(min_x3), int(min_x2)],
              "max": [int(max_x1), int(max_x2), int(max_x3), int(max_x4), int(max_x5)]}

    plt.figure(figsize=(20, 20))
    plt.plot(df.index, df["FDTG"], color="blue")
    x = result["min"] + result["max"]
    y = df["FDTG"][x]
    t = ["min_x1", "min_x2", "min_x3", "max_x1", "max_x2", "max_x3", "max_x4", "max_x5"]
    plt.scatter(x, y, color="red")
    [plt.text(i, j, k) for i, j, k in zip(x, y, t)]
    Logger.info(f"请检查特征点:\nmin:{result['min']}\nmax:{result['max']}\n(若为阻塞模式请记录数据关闭图像后进行交互)")
    plt.show(block=block)

    while True:
        a = input("更改特征点(N(n)/[max_x1-max_x5 | min_x1-min_x3]):")
        if a.upper() == "N":
            break
        else:
            v = float(input(f"{a}:"))
            key = a[:3]
            value = int(a[-1])
            result[key][value - 1] = v
    plt.close()
    Logger.info(f"已更改特征点:\nmin:{result['min']}\nmax:{result['max']}")
    with open("./chara_points.json", "w") as file:
        json.dump(result, file, indent=3)

    return result


if __name__ == '__main__':
    from data_loader import load_data, preprocess_data

    df = load_data("test/zdw.txt")
    df = preprocess_data(9.4, df, drop_first=True, a=0.03)
    x = get_chara_point(df, recal=True)
