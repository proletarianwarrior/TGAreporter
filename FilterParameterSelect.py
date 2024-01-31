# -*- coding: utf-8 -*-
# @Time : 2024/1/28 23:13
# @Author : DanYang
# @File : FilterParameterSelect.py
# @Software : PyCharm
from configparser import ConfigParser
import logging
import sys

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np

from DataLoader import _butter_filter, _inertial_filter, _load_data
from Logger import setup_logger

logger = setup_logger('select_filter_param')
cfg = ConfigParser()
cfg.read('./config.ini', encoding='utf-8')


def _create_butter_app(cfg, x, y, func):
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("xjtu热重分析实验绘图工具——butter滤波工具"),
        html.Label('N(butter滤波阶数):'),
        dcc.Slider(
            id='slider-param-1',
            min=0,
            max=50,
            step=1,
            value=cfg.getint('DataProcess', 'N'),
            marks={i: str(i) for i in range(0, 55, 5)}
        ),
        html.Label('Wn(butter截止频率):'),
        dcc.Slider(
                id='slider-param-2',
                min=0,
                max=0.3,
                step=0.005,
                value=cfg.getfloat('DataProcess', 'Wn'),
                marks={i: f'{i: .2f}' for i in np.arange(0, 0.35, 0.05)}
            ),
        html.Label('Alpha(EWMA平滑因子):'),
        dcc.Slider(
            id='slider-param-3',
            min=0,
            max=0.3,
            step=0.005,
            value=cfg.getfloat('DataProcess', 'alpha'),
            marks={i: f'{i: .2f}' for i in np.arange(0, 0.35, 0.05)}
        ),
        dcc.Graph(id='graph')
    ])

    @app.callback(
        Output('graph', 'figure'),
        [Input('slider-param-1', 'value'), Input('slider-param-2', 'value'), Input('slider-param-3', 'value')]
    )
    def update_figure(param_1, param_2, param_3):
        cfg.set('DataProcess', 'N', str(param_1))
        cfg.set('DataProcess', 'Wn', str(param_2))
        cfg.set('DataProcess', 'alpha', str(param_3))
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            cfg.write(configfile)
        d_y = np.diff(y)
        n_y = func(y, N=param_1, Wn=param_2, alpha=param_3)
        n_y = np.diff(n_y)

        trace1 = go.Scatter(
            x=x[1:],
            y=n_y,
            mode='lines',
            marker={'size': 10, 'color': 'red'},
            name='filter_DTG'
        )

        trace2 = go.Scatter(
            x=x[1:],
            y=d_y,
            mode='lines',
            marker={'size': 10, 'color': 'blue'},
            opacity=0.3,
            name='old_DTG'
        )

        layout = go.Layout(
            title=f'N={param_1} Wn={param_2: .3f}',
            xaxis={'title': 'T'},
            yaxis={'title': 'DTG', 'range': [n_y.min(), n_y.max()]},
            width=1600,
            height=1000
        )

        return {'data': [trace1, trace2], 'layout': layout}

    app.run_server(debug=False)


def _create_inertial_app(cfg, x, y, func):
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("xjtu热重分析实验绘图工具——inertial滤波工具"),
        html.Label('a(inertial惯性系数):'),
        dcc.Slider(
                id='slider-param',
                min=0,
                max=0.3,
                step=0.005,
                value=cfg.getfloat('DataProcess', 'Wn'),
                marks={i: f'{i: .2f}' for i in np.arange(0, 0.35, 0.05)}
            ),
        dcc.Graph(id='graph')
    ])

    @app.callback(
        Output('graph', 'figure'),
        [Input('slider-param', 'value')]
    )
    def update_figure(param):
        cfg.set('DataProcess', 'a', str(param))
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            cfg.write(configfile)
        d_y = np.diff(y)
        n_y = func(y, a=param)
        n_y = np.diff(n_y)

        trace1 = go.Scatter(
            x=x[1:],
            y=n_y,
            mode='lines',
            marker={'size': 10, 'color': 'red'},
            name='filter_DTG'
        ),
        trace2 = go.Scatter(
            x=x[1:],
            y=d_y,
            mode='lines',
            marker={'size': 10, 'color': 'blue'},
            opacity=0.3,
            name='old_DTG'
        ),
        layout = go.Layout(
            title=f'a={param: .3f}',
            xaxis={'title': 'T'},
            yaxis={'title': 'DTG', 'range': [n_y.min(), n_y.max()]},
            width=1600,
            height=1000
        )

        return {'data': [trace1[0], trace2[0]], 'layout': layout}

    app.run_server(debug=False)


def select_filter_param(file_path, method):
    logger.info(f'启动{method}参数选择器,请在浏览器中打开网址http://127.0.0.1:8050/')
    df = _load_data(file_path)
    T = df['温度']
    TG = df['热重']
    try:
        if method == 'butter':
            _create_butter_app(cfg, T, TG, _butter_filter)
        elif method == 'inertial':
            _create_inertial_app(cfg, T, TG, _inertial_filter)
    except:
        logger.info(f'退出{method}选择器')
    finally:
        sys.exit(0)


if __name__ == '__main__':
    from pathlib import Path
    i = Path('./data/ymt.txt')
    select_filter_param(i, 'butter')
