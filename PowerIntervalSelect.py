# -*- coding: utf-8 -*-
# @Time : 2024/1/31 17:04
# @Author : DanYang
# @File : PowerIntervalSelect.py
# @Software : PyCharm
import json
import os
import re

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

from DataLoader import _process_data, cfg


def select_power_interval(file_path):
    df = _process_data(file_path)
    T = df['温度'].values
    DTG = df['滤波后热重导数变化率'].values

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("xjtu热重分析实验绘图工具——动力反应区间选择工具"),
        dcc.Dropdown(
            id='dropdown',
            options=[
                {'label': '煤热解动力反应区间', 'value': 'mr'},
                {'label': '碳燃烧动力反应区间', 'value': 'tr'},
            ],
            value='mr'
        ),
        html.Br(),
        html.Div(
            [
            html.Button('确认', id='select-button', n_clicks=0)],
            style={'display': 'inline-block', 'font-size': '20px', 'text-align': 'center'}
        ),
        dcc.Graph(id='graph'),
        html.Label('start'),
        dcc.Slider(
            id='slider-param-1',
            min=T.min(),
            max=T.max(),
            step=0.01,
            value=float(cfg.get('DataPlot', 'coal_pyrolysis').split(',')[-1].strip()),
            marks={i: str(i) for i in range(round(T.min() / 100) * 100, round(T.max() / 100) * 100, 100)}
        ),
        html.Label('end'),
        dcc.Slider(
            id='slider-param-2',
            min=T.min(),
            max=T.max(),
            step=0.01,
            value=float(cfg.get('DataPlot', 'coal_pyrolysis').split(',')[-1].strip()),
            marks={i: str(i) for i in range(round(T.min() / 100) * 100, round(T.max() / 100) * 100, 100)}
        )
    ])

    @app.callback(
        Output('select-button', 'n_clicks'),
        [Input('select-button', 'n_clicks'), Input('dropdown', 'value'), Input('slider-param-1', 'value'), Input('slider-param-2', 'value')]
    )
    def change_feature(param_1, param_2, param_3, param_4):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id != 'select-button':
            return param_1
        if param_2 == 'mr':
            cfg.set('DataPlot', 'coal_pyrolysis', f'{param_3: .2f},{param_4: .2f}')
        if param_2 == 'tr':
            cfg.set('DataPlot', 'carbon_combustion', f'{param_3: .2f},{param_4: .2f}')
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            cfg.write(configfile)
        return param_1

    @app.callback(
        Output('graph', 'figure'),
        [Input('dropdown', 'value'), Input('slider-param-1', 'value'), Input('slider-param-2', 'value')]
    )
    def update_figure(param_1, param_2, param_3):
        if param_1 == 'mr':
            color = 'peru'
        elif param_1 == 'tr':
            color = 'firebrick'

        trace1 = go.Scatter(
            x=T,
            y=DTG,
            mode='lines',
            marker={'size': 10, 'color': 'red'},
            name='filter_DTG'
        )
        x1 = T[T <= param_2][-1] if len(T[T <= param_2]) > 0 else T[0]
        y1 = DTG[T <= param_2][-1] if len(T[T <= param_2]) > 0 else DTG[0]
        x2 = T[T <= param_3][-1] if len(T[T <= param_3]) > 0 else T[0]
        y2 = DTG[T <= param_3][-1] if len(T[T <= param_3]) > 0 else DTG[0]

        trace2 = go.Scatter(
            x=[x1],
            y=[y1],
            mode='markers',
            marker={'size': 10, 'color': color, 'symbol': 'x'},
            name='start_point'
        )
        trace3 = go.Scatter(
            x=[x2],
            y=[y2],
            mode='markers',
            marker={'size': 10, 'color': color, 'symbol': 'x'},
            name='end_point'
        )
        trace4 = go.Scatter(
            x=[x1, x1],
            y=[DTG.min(), DTG.max()],
            mode='lines',
            marker={'size': 8, 'color': color},
            line={'dash': 'dash'},
            name='start_line'
        )
        trace5 = go.Scatter(
            x=[x2, x2],
            y=[DTG.min(), DTG.max()],
            mode='lines',
            marker={'size': 8, 'color': color},
            line={'dash': 'dash'},
            name='end_line'
        )
        layout = go.Layout(
            title=f'x1={param_2}\tx2={param_3}',
            xaxis={'title': 'T'},
            yaxis={'title': 'DTG'},
            width=1600,
            height=1000
        )
        return {'data': [trace1, trace2, trace3, trace4, trace5], 'layout': layout}

    @app.callback(
        Output('slider-param-1', 'value'),
        [Input('dropdown', 'value')]
    )
    def a1(param):
        if param == 'mr':
            p = cfg.get('DataPlot', 'coal_pyrolysis')
            return float(p.split(',')[0].strip())
        else:
            p = cfg.get('DataPlot', 'carbon_combustion')
            return float(p.split(',')[0].strip())

    @app.callback(
        Output('slider-param-2', 'value'),
        [Input('dropdown', 'value')]
    )
    def a1(param):
        if param == 'mr':
            p = cfg.get('DataPlot', 'coal_pyrolysis')
            return float(p.split(',')[-1].strip())
        else:
            p = cfg.get('DataPlot', 'carbon_combustion')
            return float(p.split(',')[-1].strip())

    app.run_server(debug=False)


if __name__ == '__main__':
    from pathlib import Path
    file_path = Path('./data/ymt.txt')
    select_feature_points(file_path)
