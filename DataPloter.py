# -*- coding: utf-8 -*-
# @Time : 2024/1/29 23:09
# @Author : DanYang
# @File : DataPloter.py
# @Software : PyCharm
import os
import json
import time

import matplotlib.pyplot as plt
import numpy as np
import scienceplots
import matplotlib

from DataLoader import _process_data, cfg
from Logger import setup_logger

logger = setup_logger('plot_data')
print(f"\033[92m{cfg.get('DataLoading', 'signature')}\033[0m")
time.sleep(0.2)


class DataPloter:
    def __init__(self, file_path):
        self.name = file_path.name.split('.')[0]
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'

        if os.path.exists('image'):
            pass
        else:
            os.mkdir('image')
        logger.info('图像文件被保存至image文件夹')

        df = _process_data(file_path)
        self.T = df['温度'].values
        self.TG = df['热重'].values
        self.ODTG = df['原始热重导数变化率'].values
        self.NDTG = df['滤波后热重导数变化率'].values

        self.width = cfg.getfloat('DataPlot', 'width')
        self.height = cfg.getfloat('DataPlot', 'height')
        self.dpi = cfg.getfloat('DataPlot', 'dpi')

        with open('feature_points.json', 'r') as file:
            self.feature_points = json.load(file)[0]

        self._save_data_for_unite_plot()

    def __enter__(self):
        plt.style.context(['science', 'ieee'])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close()
        return

    def _save_data_for_unite_plot(self):
        if not os.path.exists('unite'):
            os.mkdir('unite')
        if not os.path.exists(f'./unite/{self.name}_unite.json'):
            with open(f'./unite/{self.name}_unite.json', 'w') as file:
                template = [{
                    'TG': {},
                    'DTG': {},
                    'TG_DTG': {},
                    'unite': {}
                }]
                json.dump(template, file, indent=2)
        with open(f'./unite/{self.name}_unite.json', 'r') as file:
            data = json.load(file)

        def cal_detail(name):
            start = float(cfg.get('DataPlot', name).split(',')[0].strip())
            end = float(cfg.get('DataPlot', name).split(',')[-1].strip())
            x = 1 / (self.T[(self.T <= end) & (start <= self.T)] + 273.15)
            T_min, T_max = 1 / x[0], 1 / x[-1]
            y = np.log(-self.NDTG[(self.T <= end) & (start <= self.T)])
            k = np.polyfit(x, y, 1)
            A, b = k[0], k[1]
            E = abs(8.314 * A)
            k0 = np.exp(b)
            y_fit = A * x + b
            TSS = np.sum((y - np.mean(y)) ** 2)
            RSS = np.sum((y - y_fit) ** 2)
            R_squared = 1 - (RSS / TSS)
            return {
                "T_min": T_min,
                "T_max": T_max,
                "A": A,
                "b": b,
                "R_square": R_squared,
                "E": E,
                "k0": k0,
                "x": list(x),
                "y": list(y)
            }
        data[0]['unite']['coal_pyrolysis'] = cal_detail('coal_pyrolysis')
        data[0]['unite']['carbon_combustion'] = cal_detail('carbon_combustion')
        with open(f'./unite/{self.name}_unite.json', 'w') as file:
            json.dump(data, file, indent=2)
        logger.info(f'{self.name}相关数据将被保存至unite/{self.name}_unite.json')

    def _format_exponent(self, ax, axis='y', expo=None, x_pos=0.0, direction='left'):
        ax.ticklabel_format(axis=axis, style='sci', scilimits=(-2, 6))

        if axis == 'y':
            ax_axis = ax.yaxis
            x_pos = x_pos
            y_pos = 1.0
            horizontalalignment = direction
            verticalalignment = 'bottom'
        elif axis == 'both':
            self._format_exponent(ax, axis='x')
            self._format_exponent(ax, axis='y', x_pos=x_pos, direction=direction)
            return ax
        else:
            ax_axis = ax.xaxis
            x_pos = 1.07
            y_pos = 0.02
            horizontalalignment = 'right'
            verticalalignment = 'top'

        plt.tight_layout()

        offset = ax_axis.get_offset_text().get_text()

        if len(offset) > 0:
            minus_sign = u'\u2212'
            expo = float(offset.replace(minus_sign, '-').split('e')[-1]) if not expo else expo
            offset_text = r'x$\mathregular{10^{%d}}$' % expo

            ax_axis.offsetText.set_visible(False)

            ax.text(x_pos, y_pos, offset_text, transform=ax.transAxes,
                    horizontalalignment=horizontalalignment,
                    verticalalignment=verticalalignment)
        return ax

    def plot_TG(self, **kwargs):
        width = kwargs.get('width', self.width)
        height = kwargs.get('width', self.height)
        dpi = kwargs.get('width', self.dpi)
        show_inflexion = kwargs.get('show_inflexion', False)
        show_min = kwargs.get('show_min', True)

        fig = plt.figure(figsize=(width, height), dpi=dpi)
        plt.plot(self.T, self.TG, color='firebrick', label='TG')
        if show_inflexion:
            DTG = np.abs(np.diff(np.cumsum(self.NDTG) * cfg.getfloat('DataProcess', 'weight'), 2))
            n = np.argmin(DTG)
            plt.scatter(self.T[n], self.TG[n], s=30, label='inflexion point', marker='x', c='tan')
            plt.text(self.T[n], self.TG[n], f'({self.T[n] :.2f},{self.TG[n]: .2f})', ha='center', va='bottom',
                     fontdict={'size': 8})
            with open(f'unite/{self.name}_unite.json', 'r') as file:
                data = json.load(file)
            data[0]['TG']['TG_inflexion'] = [self.T[n], self.TG[n]]
            with open(f'unite/{self.name}_unite.json', 'w') as file:
                json.dump(data, file, indent=2)

        if show_min:
            m = np.argmin(self.TG)
            plt.scatter(self.T[m], self.TG[m], s=30, label='min point', marker='x', c='deepskyblue')
            plt.text(self.T[m], self.TG[m], f'({self.T[m] :.2f},{self.TG[m]: .2f})', ha='center', va='bottom',
                     fontdict={'size': 8})
            with open(f'unite/{self.name}_unite.json', 'r') as file:
                data = json.load(file)
            data[0]['TG']['TG_min'] = [self.T[m], self.TG[m]]
            with open(f'unite/{self.name}_unite.json', 'w') as file:
                json.dump(data, file, indent=2)
        plt.minorticks_on()

        plt.xlabel('T/$\degree\mathrm{C}$')
        plt.ylabel('TG/mg')
        plt.grid()
        plt.legend(loc=1)
        plt.savefig('image/TG-T.jpg', bbox_inches='tight')
        logger.info(f'成功保存TG-T图像')

    def plot_DTG(self, **kwargs):
        width = kwargs.get('width', self.width)
        height = kwargs.get('width', self.height)
        dpi = kwargs.get('width', self.dpi)

        fig = plt.figure(figsize=(width, height), dpi=dpi)
        ax = plt.subplot()
        plt.minorticks_on()
        plt.plot(self.T, self.NDTG, color='firebrick', label='filter DTG')
        plt.plot(self.T, self.ODTG, color='indianred', label='original DTG', alpha=0.25)

        sep = (self.NDTG.max() - self.NDTG.min()) / 20
        y_min = self.NDTG.min() - sep
        y_max = self.NDTG.max() + sep
        plt.ylim([y_min, y_max])

        feature_points = np.array(list(self.feature_points.values())).reshape((3, 3))
        feature_keys = np.array(list(self.feature_points.keys())).reshape((3, 3))
        colors = ['powderblue', 'peru', 'rebeccapurple']
        dbs = ['deepskyblue', 'brown', 'purple']
        texts = ['Water Separation', 'Coal Pyrolysis', 'Carbon Combustion']
        data_texts = ['water_separation', 'coal_pyrolysis', 'carbon_combustion']
        with open(f'unite/{self.name}_unite.json', 'r') as file:
            data = json.load(file)
        for keys, line, color, db, text, t in zip(feature_keys, feature_points, colors, dbs, texts, data_texts):
            line = line[np.argsort(keys)]
            data[0]['DTG'][t] = [line[-1], line[0]]
            plt.fill_betweenx([y_min, y_max], line[-1], line[0], color=color, alpha=0.4)
            plt.text((line[-1] + line[0]) / 2, y_max - 3 * sep, text, color='black', ha='center', fontsize=12)
            for x in line:
                plt.scatter([x], [self.NDTG[self.T <= x][-1] if len(self.NDTG[self.T <= x]) > 0 else self.NDTG[0]],
                            marker='x', color=db)
                plt.axvline(x, color='dimgrey', linestyle='--', linewidth=1)

        self._format_exponent(ax)
        plt.xlabel('T/$\degree\mathrm{C}$')
        plt.ylabel('DTG/s')
        plt.grid()
        plt.legend(loc=1)
        plt.savefig('image/DTG-T.jpg', bbox_inches='tight')

        with open(f'unite/{self.name}_unite.json', 'w') as file:
            json.dump(data, file, indent=2)

        logger.info(f'成功保存DTG-T图像')

    def plot_TG_DTG(self, **kwargs):
        width = kwargs.get('width', self.width)
        height = kwargs.get('width', self.height)
        dpi = kwargs.get('width', self.dpi)
        DTG_color = kwargs.get('DTG_color', cfg.get('DataPlot', 'DTG_color'))
        TG_color = kwargs.get('TG_color', cfg.get('DataPlot', 'TG_color'))

        fig = plt.figure(figsize=(width, height), dpi=dpi)
        ax1 = plt.subplot()
        ax2 = plt.twinx(ax1)

        ax1.minorticks_on()
        ax2.minorticks_on()
        line2 = ax2.plot(self.T, self.NDTG, color=DTG_color, label='filter DTG', linestyle='--')
        line1 = ax1.plot(self.T, self.TG, color=TG_color, label='TG')
        sep1 = (self.TG.max() - self.TG.min()) / 20
        sep2 = (self.NDTG.max() - self.NDTG.min()) / 20
        y_min_1, y_max_1 = self.TG.min() - sep1, self.TG.max() + sep1
        y_min_2, y_max_2 = self.NDTG.min() - sep2, self.NDTG.max() + sep2

        x_ps = self.feature_points['ps']
        x_bm = self.feature_points['bm']
        x_be = self.feature_points['be']
        y_bm = self.TG[self.T <= x_bm][-1]
        y_ps = self.TG[self.T <= x_ps][-1]
        y_be = self.TG[self.T <= x_be][-1]
        k = ((self.TG[self.T >= x_bm][:5] - self.TG[self.T <= x_bm][-5:]) /
             (self.T[self.T >= x_bm][:5] - self.T[self.T <= x_bm][-5:])).mean()
        y0 = np.linspace(y_min_1, y_max_1, 1000)
        x0 = (y0 - y_bm) / k + x_bm
        ax1.plot(x0, y0, color='red', linewidth=0.5)
        ax1.plot([x_ps, (y_ps - y_bm) / k + x_bm], [y_ps, y_ps], color='red', linewidth=0.7)
        ax1.plot([x_be, (y_be - y_bm) / k + x_bm], [y_be, y_be], color='red', linewidth=0.7)
        ax1.plot([x_bm, x_bm], [y_min_1, y_bm], color='darkred', linewidth=0.7)
        ax1.text((y_ps - y_bm) / k + x_bm, y_ps, 'i', ha='left', va='bottom', fontsize=12)
        ax1.text((y_be - y_bm) / k + x_bm, y_be, 'f', ha='right', va='top', fontsize=12)
        ax1.text(x_bm, y_bm, 'A', ha='left', va='bottom', fontsize=12)
        ax1.text((y_ps - y_bm) / k / 2 + x_bm, (y_bm + y_ps) / 2, '$L_2$', ha='left', va='bottom', fontsize=12)
        ax1.text(x_ps, y_ps, '$L_1$', ha='center', va='bottom', fontsize=12)
        ax1.text(x_be, y_be, '$L_3$', ha='center', va='bottom', fontsize=12)

        ax1.set_ylim([y_min_1, y_max_1])
        ax2.set_ylim([y_min_2, y_max_2])
        ax1.set_xlabel('T/$\degree\mathrm{C}$')
        ax1.set_ylabel('TG/mg', color=TG_color)
        ax2.set_ylabel('DTG/s', color=DTG_color)
        ax1.grid()
        lines = line1 + line2
        plt.legend(lines, [i.get_label() for i in lines], loc=1)
        ax2.spines['left'].set_color(TG_color)
        ax2.spines['right'].set_color(DTG_color)
        ax1.tick_params(axis='y', colors=TG_color)
        ax2.tick_params(axis='y', colors=DTG_color)
        self._format_exponent(ax2, x_pos=1.0, direction='right')
        plt.savefig('image/TG-DTG-T.jpg', bbox_inches='tight')

        with open(f'unite/{self.name}_unite.json', 'r') as file:
            data = json.load(file)
        w0 = cfg.getfloat('DataProcess', 'weight')
        data[0]['TG_DTG'] = {
            'T_i': (y_ps - y_bm) / k + x_bm,
            'T_f': (y_be - y_bm) / k + x_bm,
            'T_p': x_bm,
            'v_p': abs(self.NDTG.min()),
            'v_mean': (self.T.max() - self.T.min()) / (len(self.T) - 1) / cfg.getfloat('DataProcess', 'sep_time') * \
                      (y_ps - y_be) / w0 / (y_be - y_ps) * k * 60 * 100
        }
        with open(f'unite/{self.name}_unite.json', 'w') as file:
            json.dump(data, file, indent=2)

        logger.info(f'成功保存TG-DTG-T图像')

    def _plot_unite(self, method, **kwargs):
        width = kwargs.get('width', self.width)
        height = kwargs.get('width', self.height)
        dpi = kwargs.get('width', self.dpi)
        labels = kwargs.get('labels', 'default')

        ofiles = os.listdir('unite')
        files = ['unite/' + i for i in ofiles]
        colors = [matplotlib.colormaps.get_cmap('Accent')(i) for i in range(len(files))]

        fig = plt.figure(figsize=(width, height), dpi=dpi)
        plt.minorticks_on()
        for i in range(len(files)):
            if labels == "default":
                label = ofiles[i].split('_')[0]
            else:
                label = labels[i]
            with open(files[i], 'r') as file:
                data = json.load(file)
            if method == 'coal_pyrolysis' or method == 'mr':
                name = 'coal_pyrolysis'
                data = data[0]['unite']['coal_pyrolysis']
                x = data['x']
                y = data['y']
                A = data['A']
                b = data['b']
            elif method == 'carbon_combustion' or method == 'tr':
                name = 'carbon_combustion'
                data = data[0]['unite']['carbon_combustion']
                x = data['x']
                y = data['y']
                A = data['A']
                b = data['b']
            else:
                raise NameError
            plt.plot(x, y, color=colors[i], label=label)
            x0 = np.linspace(min(x), max(x), 1000)
            y0 = A * x0 + b
            plt.plot(x0, y0, color='black')

        ax = plt.subplot()
        plt.grid()
        plt.legend(loc=1)
        self._format_exponent(ax, axis='both')
        plt.savefig(f'image/{name}.jpg', bbox_inches='tight')
        logger.info(f'成功保存unite {name}图像')

    def plot_unite(self, **kwargs):
        self._plot_unite(method='mr', **kwargs)
        self._plot_unite(method='tr', **kwargs)


if __name__ == '__main__':
    from pathlib import Path

    data_path = Path('./data/ymt.txt')
    ploter = DataPloter(data_path)
    ploter.plot_unite()
