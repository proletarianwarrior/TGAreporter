from pathlib import Path

from FilterParameterSelect import select_filter_param
from FeaturePointSelect import select_feature_points
from PowerIntervalSelect import select_power_interval
from DocReporter import create_doc

file_path = Path('./data/ck.txt')
# select_filter_param(file_path, method='butter')  # 滤波参数选择器
# select_feature_points(file_path)  # 特征点选择器
# select_power_interval(file_path)  # 动力反应区间选择器
create_doc(file_path)  # 生成绘图报告
