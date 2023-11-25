# -*- coding: utf-8 -*-
# @Time : 2023/11/23 22:23
# @Author : DanYang
# @File : test.py
# @Software : PyCharm
import json

import pandas as pd
import numpy as np


def save_csv(file_name, method):
    with open(f"./file/{file_name}_{method}.json", "r") as file:
        data = json.load(file)
    x = data["1/T"]
    y = data["lnk"]
    df = pd.DataFrame(data=np.array([x, y]).T, columns=["1/T", "lnk"])
    df.to_excel(f"{file_name}_{method}.xlsx")


save_csv("ymt", "burn")