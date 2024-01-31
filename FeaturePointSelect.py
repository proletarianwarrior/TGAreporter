# -*- coding: utf-8 -*-
# @Time : 2024/1/29 18:20
# @Author : DanYang
# @File : FeaturePointSelect.py
# @Software : PyCharm
import json
import os
import re

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

from DataLoader import _process_data


def select_feature_points(file_path):
    df = _process_data(file_path)
    T = df['温度'].values
    DTG = df['滤波后热重导数变化率'].values

    if not os.path.exists('feature_points.json'):
        param_dict = [{
            'ws':  300,
            'wm': 300,
            'we': 300,
            'ps': 300,
            'pm': 300,
            'pe': 300,
            'bm': 300,
            'bs': 300,
            'be': 300,
        }]
        with open('feature_points.json', 'w') as file:
            json.dump(param_dict, file)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("xjtu热重分析实验绘图工具——特征点选择工具"),
        dcc.Dropdown(
            id='dropdown',
            options=[
                {'label': '全部特征点', 'value': 'tt'},
                {'label': '水蒸发开始', 'value': 'ws'},
                {'label': '水蒸发剧烈', 'value': 'wm'},
                {'label': '水蒸发结束', 'value': 'we'},
                {'label': '煤热解开始', 'value': 'ps'},
                {'label': '煤热解剧烈', 'value': 'pm'},
                {'label': '煤热解结束', 'value': 'pe'},
                {'label': '碳燃烧开始', 'value': 'bs'},
                {'label': '碳燃烧最大', 'value': 'bm'},
                {'label': '碳燃烧结束', 'value': 'be'}
            ],
            value='tt'
        ),
        html.Br(),
        html.Div(
            [html.Label('x:'),
            dcc.Input(
                id='input-box',
                type='text',
                placeholder='选择的横坐标',
                value=''
            ),
            html.Button('确认', id='select-button', n_clicks=0)],
            style={'display': 'inline-block', 'font-size': '20px'}
        ),
        dcc.Graph(id='graph'),
        html.Label('x轴'),
        dcc.Slider(
            id='slider-param',
            min=T.min(),
            max=T.max(),
            step=0.01,
            value=500,
            marks={i: str(i) for i in range(round(T.min() / 100) * 100, round(T.max() / 100) * 100, 100)}
        )
    ])

    @app.callback(
        Output('select-button', 'n_clicks'),
        [Input('select-button', 'n_clicks'), Input('dropdown', 'value'), Input('slider-param', 'value')]
    )
    def change_feature(param_1, param_2, param_3):
        if param_2 == 'tt':
            return param_1
        with open('feature_points.json', 'r') as file:
            param_dict = json.load(file)
        param_dict[0][param_2] = param_3
        with open('feature_points.json', 'w') as file:
            json.dump(param_dict, file)
        return param_1

    @app.callback(
        Output('graph', 'figure'),
        [Input('slider-param', 'value'), Input('dropdown', 'value')]
    )
    def update_figure(param_1, param_2):
        if param_2.startswith('w'):
            color = 'blue'
        elif param_2.startswith('p'):
            color = 'purple'
        elif param_2.startswith('b'):
            color = 'black'
        else:
            color = 'grey'
            with open('feature_points.json', 'r') as file:
                param_dict = json.load(file)
            trace1 = go.Scatter(
                x=T,
                y=DTG,
                mode='lines',
                marker={'size': 10, 'color': 'red'},
                name='filter_DTG'
            )
            x = []
            y = []
            for i in param_dict[0].values():
                x.append(T[T <= i][-1] if len(T[T <= i]) > 0 else T[0])
                y.append(DTG[T <= i][-1] if len(T[T <= i]) > 0 else DTG[0])

            trace2 = go.Scatter(
                x=x,
                y=y,
                mode='markers',
                marker={'size': 10, 'color': color, 'symbol': 'x'},
                name='select_point'
            )
            layout = go.Layout(
                title=f'特征点总览',
                xaxis={'title': 'T'},
                yaxis={'title': 'DTG'},
                width=1600,
                height=1000
            )
            return {'data': [trace1, trace2], 'layout': layout}

        trace1 = go.Scatter(
            x=T,
            y=DTG,
            mode='lines',
            marker={'size': 10, 'color': 'red'},
            name='filter_DTG'
        )
        x = T[T <= param_1][-1] if len(T[T <= param_1]) > 0 else T[0]
        y = DTG[T <= param_1][-1] if len(T[T <= param_1]) > 0 else DTG[0]

        trace2 = go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker={'size': 10, 'color': color, 'symbol': 'x'},
            name='select_point'
        )
        trace3 = go.Scatter(
            x=[x, x],
            y=[DTG.min(), y],
            mode='lines',
            marker={'size': 8, 'color': color},
            line={'dash': 'dash'},
            name='select_line'
        )
        layout = go.Layout(
            title=f'x={x: .4f}\ty={y: .4e}',
            xaxis={'title': 'T'},
            yaxis={'title': 'DTG'},
            width=1600,
            height=1000
        )
        return {'data': [trace1, trace2, trace3], 'layout': layout}

    @app.callback(
        Output('slider-param', 'value'),
        [Input('dropdown', 'value'), Input('input-box', 'value')]
    )
    def update_slider(param_1, param_2):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == 'input-box':
            if param_1 == 'tt':
                return T.min()
            if bool(re.match(r'^[-+]?\d+[.]?\d*$', param_2)):
                return float(param_2)
        elif triggered_id == 'dropdown':
            if param_1 == 'tt':
                return T.min()
            with open('feature_points.json', 'r') as file:
                param_dict = json.load(file)
            return param_dict[0][param_1]

    app.run_server(debug=False)


if __name__ == '__main__':
    from pathlib import Path
    file_path = Path('./data/ymt.txt')
    select_feature_points(file_path)

