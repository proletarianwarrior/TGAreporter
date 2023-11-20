# -*- coding: utf-8 -*-
# @Time : 2023/11/19 15:27
# @Author : DanYang
# @File : data_ploter.py
# @Software : PyCharm
from typing import Union

import pandas as pd
from plotnine import *
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

from logger import Logger
from data_parser import get_chara_point
from data_loader import preprocess_data


class DataPloter:
    def __init__(self, w0: float, file_path: Union[Path, str], **kwargs):
        self.Tsep = kwargs.get("Tsep", 50)
        self.TGsep = kwargs.get("TGsep", 2)
        self.FDTGsep = kwargs.get("FDTGsep", 1e-4)

        self.width = kwargs.get("width", 15)
        self.height = kwargs.get("height", 10)

        self.w0 = w0
        self.df = preprocess_data(w0, file_path, **kwargs)
        self.chara_points = get_chara_point(self.df, **kwargs)

        columns = self.df.columns
        self.T_name, self.TG_name, self.TG_W_name, self.DTG_name, self.FDTG_name = tuple(columns.tolist())
        self.T = self.df[self.T_name]
        self.TG = self.df[self.TG_name]
        self.TG_W = self.df[self.TG_W_name]
        self.DTG = self.df[self.DTG_name]
        self.FDTG = self.df[self.FDTG_name]
        self.t = self.df.index

    @staticmethod
    def get_min_max(data: Union[np.ndarray, pd.Series], sep: Union[int, float]):
        data_max = (data.max() // sep + int(data.max() % sep != 0)) * sep
        data_min = (data.min() // sep) * sep

        return data_min, data_max

    def plot_TG(self, show_fig=False):
        if show_fig:
            dpi = 100
        else:
            dpi = 200
        x_min, x_max = self.get_min_max(self.T, self.Tsep)
        y_min, y_max = self.get_min_max(self.TG, self.TGsep)
        x_label = np.arange(x_min, x_max + self.Tsep, self.Tsep).astype(int)
        y_label = np.arange(y_min, y_max + self.TGsep, self.TGsep)
        y_label = np.hstack((y_label, round(self.TG.min(), 2)))

        base_plot = (ggplot(self.df, aes(x=self.T_name, y=self.TG_name)) +
                     # watermark("./watermark/watermark.jpg", alpha=0.2) +
                     geom_line(color="#e34a33", size=1) +
                     theme_light() +
                     scale_x_continuous(name="T/\u2103", breaks=x_label, labels=x_label) +
                     scale_y_continuous(name="TG/mg", breaks=y_label, labels=y_label) +
                     theme(text=element_text(size=16, family="Times New Roman"),
                           plot_title=element_text(size=20),
                           axis_text_x=element_text(size=14),
                           axis_text_y=element_text(size=14)
                           ) +
                     ggtitle("TG-T")
                     )
        base_plot.save("./image/TG.png", dpi=dpi, width=self.width, height=self.height)
        Logger.info(f"保存TG数据")
        if show_fig:
            print(base_plot)

    def plot_DTG(self, show_fig=False):
        if show_fig:
            dpi = 100
        else:
            dpi = 200
        X_min = self.chara_points["min"]
        X_max = self.chara_points["max"]
        x_min, x_max = self.get_min_max(self.T, self.Tsep)
        y_min, y_max = self.get_min_max(self.FDTG, self.FDTGsep)
        x_label = np.arange(x_min, x_max + self.Tsep, self.Tsep).astype(int)
        x_label = np.hstack((x_label, [self.T[i] for i in X_min]))
        n_x_label = [f"{i: .2f}" for i in x_label]
        y_label = np.arange(y_min, y_max + self.FDTGsep, self.FDTGsep)
        y_label = np.hstack((y_label, self.FDTG.min()))
        n_y_label = []
        for i in y_label:
            if abs(i) < 1e-10:
                n_y_label.append(f"{0:.2e}")
            else:
                n_y_label.append(f"{i:.2e}")
        point_df = pd.DataFrame(columns=["p_x", "p_y"])
        point_df["p_x"] = [self.T[i] for i in X_max + X_min]
        point_df["p_y"] = [self.FDTG[i] for i in X_max + X_min]

        base_plot = (ggplot(self.df, aes(x=self.T_name, y=self.FDTG_name)) +
                     # watermark("./watermark/watermark.jpg", alpha=0.2) +
                     geom_line(aes(x=self.T_name, y=self.DTG_name), color="#F0AEA9", size=0.7, alpha=0.8) +
                     geom_line(color="#FC1944", size=1) +
                     geom_point(aes(x="p_x", y="p_y"), data=point_df, size=2.5, shape="o", show_legend=False, color="black")
                     )
        for x in X_max:
            base_plot += geom_vline(aes(xintercept=self.T[x]), linetype="--", color="grey")
        for x in X_min:
            base_plot += geom_vline(aes(xintercept=self.T[x]), linetype="--", color="red")
        text_df = pd.DataFrame(columns=["x", "y", "label"])
        for i, j, c, t in zip([X_max[0], X_max[2], X_max[3]], [X_max[1], X_max[3], X_max[4]],
                              ["#78B4E0", "#FF7200", "#9E2F68"],
                              ["water\nseparating", "coal\ndissolving", "carbon\nburning"]):
            i = self.T[i]
            j = self.T[j]
            text_df = text_df.append({"x": (i + j) / 2, "y": (self.FDTG.max() - self.FDTG.min()) * 1 / 4 + self.FDTG.min(),
                                      "label": t}, ignore_index=True)
            base_plot += geom_ribbon(aes(x=[i, j], ymin=[self.FDTG.min()] * 2, ymax=[self.FDTG.max()] * 2), fill=c,
                                     data=self.df.iloc[:2, :], alpha=0.4)

        base_plot += geom_text(aes(x="x", y="y", label="label"), data=text_df, show_legend=False, size=15,
                               family="Times New Roman")
        base_plot += scale_x_continuous(name="T/\u2103", breaks=x_label, labels=n_x_label, limits=[x_label.min(), x_label.max()])
        base_plot += scale_y_continuous(name="DTG/s", breaks=y_label, labels=n_y_label, limits=[y_label.min(), y_label.max()])
        base_plot += theme_light()
        base_plot += theme(text=element_text(size=12, family="Times New Roman"),
                           plot_title=element_text(size=18),
                           axis_text_x=element_text(rotation=90, hjust=0.5))
        base_plot += ggtitle("DTG-T")

        base_plot.save("./image/DTG.png", dpi=dpi, width=self.width, height=self.height)
        Logger.info(f"保存DTG数据")
        if show_fig:
            print(base_plot)

    def plot_TG_DTG(self, show_fig=False):
        if show_fig:
            dpi = 100
        else:
            dpi = 200
        sns.set_style("whitegrid")
        fig, ax = plt.subplots(layout='constrained', figsize=(15, 10), dpi=dpi)
        ax.plot(self.T, self.TG, color="#e34a33")
        ax.set_ylabel("TG/mg", font={"family": "Times New Roman", "size": 16})
        ax.set_xlabel("T/°C", font={"family": "Times New Roman", "size": 16})
        ax.grid(visible=False)
        TG_ylim = self.get_min_max(self.TG, self.TGsep)
        ax.set_ylim(TG_ylim)

        ax2 = ax.twinx()
        ax2.plot(self.T, self.FDTG, color="#3182bd", linestyle="--")
        ax2.set_ylabel("DTG/s", font={"family": "Times New Roman", "size": 16})
        ax2.grid(visible=False)
        FDTG_ylim = self.get_min_max(self.FDTG, self.FDTGsep)
        ax2.set_ylim(FDTG_ylim)

        ax.tick_params(axis='y', direction='in')
        ax2.tick_params(axis='y', direction='in')

        T_xlim = self.get_min_max(self.T, self.Tsep)
        plt.xlim(T_xlim)

        X_min, X_max = self.chara_points["min"], self.chara_points["max"]

        n1 = self.TG[int(X_min[2] / 2):X_min[2]].argmax() + self.TG.index[0] + int(X_min[2] / 2)
        x1 = self.T[n1]
        y1 = self.TG[n1]
        n2 = X_min[2]
        x2 = self.T[n2]
        y2 = self.FDTG[n2]
        xs = np.arange(n2-10, n2+10)
        k = np.polyfit([self.T[x] for x in xs], [self.TG[x] for x in xs], 1)
        y0 = np.linspace(TG_ylim[0], TG_ylim[1], 1000)
        x0 = (y0 - k[1]) / k[0]
        x3 = (y1 - k[1]) / k[0]
        n4 = self.TG[X_min[2]:].argmin() + self.TG.index[0] + X_min[2]
        x4 = self.T[n4]
        y4 = self.TG[n4]
        x5 = (y4 - k[1]) / k[0]

        ax.hlines(y1, x1, x3, alpha=0.8, color="orange", linewidth=0.6)
        ax.hlines(y4, x5, x4, alpha=0.8, color="orange", linewidth=0.6)
        ax2.hlines(y2, x2, T_xlim[-1], alpha=0.8, color="orange", linewidth=0.6)
        ax.vlines(x2, TG_ylim[0], y2, alpha=0.8, color="orange", linewidth=0.6)
        ax.vlines(x5, TG_ylim[0], y4, alpha=0.8, color="red", linewidth=0.6)
        ax.plot(x0, y0, alpha=0.8, color="orange", linewidth=0.6)
        ax.vlines(x3, TG_ylim[0], y1, alpha=0.8, color="red", linewidth=0.6)

        xticks = np.arange(T_xlim[0], T_xlim[1], self.Tsep)
        yticks = np.arange(FDTG_ylim[0], FDTG_ylim[1], self.FDTGsep)
        yticks[-1] = 0
        yticks = np.hstack((yticks, y2))
        xticks = np.hstack((xticks, [round(x3, 2), round(x5, 2), round(x2, 2)]))
        ax.set_xticks(xticks, xticks, rotation=90)
        ax2.set_yticks(yticks, [f"{i: .2e}" for i in yticks])

        ax.text(x3, y1, "i", font={"family": "Times New Roman", "size": 15})
        ax.text(x5, y4, "f", font={"family": "Times New Roman", "size": 15})
        beta = np.diff(self.T).mean() * 60
        aif = (y1 - y4) / self.w0
        Tif = x5 - x3
        v = beta * aif / Tif
        ax.text(70, -6, f"combustion point\t$T_i$={round(x3, 2)}\nignition point\t$T_f$={round(x5, 2)}\n"
                          f"Maximum burning rate\t$v_p$={y2:.2e}\n"
                          f"Maximum burning temperature\t$T_p$={round(x2, 2)}\n"
                          f"Average burning rate\t$\overline{{v}}$={round(100 * v, 3)}%",
                font={"family": "Times New Roman", "size": 15})
        plt.title("DTG/TG-T", font={"family": "Times New Roman", "size": 18})
        plt.savefig("./image/DTG-TG.png")
        Logger.info(f"保存DTG-TG数据")
        if show_fig:
            plt.show()

    def plot_fit_TG(self, method: str = "", show_fig=False, Tlim: Union[list, None] = None):
        if show_fig:
            dpi = 100
        else:
            dpi = 200
        X_min, X_max = self.chara_points["min"], self.chara_points["max"]
        if method == "hot":
            x_sep_1, x_sep_2 = X_max[2], X_min[1]
        elif method == "burn":
            x_sep_1, x_sep_2 = X_max[3], X_min[2]
        elif Tlim:
            x_sep_1 = sum(self.df["T"] < Tlim[0])
            x_sep_2 = len(self.df["T"]) - sum(self.df["T"] > Tlim[1])
        else:
            raise TypeError("请输入正确的区间名称!")
        n_df = self.df.iloc[x_sep_1:x_sep_2, :]
        n_df["1/T"] = 1 / (n_df[self.T_name] + 273.15)
        n_df["lnk"] = np.log(n_df[self.FDTG_name].abs())
        x = np.linspace(n_df["1/T"].min(), n_df["1/T"].max(), len(n_df["1/T"]))
        k = np.polyfit(n_df["1/T"], n_df["lnk"], 1)
        y = k[0] * x + k[1]
        n_df["x"] = x
        n_df["y"] = y
        corr = n_df["lnk"].corr(k[0] * n_df["1/T"] + k[1])

        text_x = 1 / 3 * (n_df["1/T"].max() - n_df["1/T"].min()) + n_df["1/T"].min()
        text_y = 1 / 3 * (n_df["lnk"].max() - n_df["lnk"].min()) + n_df["lnk"].min()

        Tmin = round(n_df["T"].min() + 273.15, 2)
        Tmax = round(n_df["T"].max() + 273.15, 2)
        E = -k[0] * 8.314
        k0 = np.exp(k[1])

        base_plot = (ggplot(n_df, aes(x="1/T", y="lnk")) +
                     # watermark("./watermark/watermark.jpg", alpha=0.2) +
                     geom_line(color="#FFE14D", size=1) +
                     geom_line(aes(x="x", y="y"), color="black", size=0.8) +
                     annotate("text", x=text_x, y=text_y,
                              label=f"y={round(k[0], 2)}x+{round(k[1], 2)}\nR={round(corr, 3)}"
                                    f"\nT$\in$[{Tmin}, {Tmax}]\nE={E: .2f}\nk0={k0:.2f}", size=15) +
                     theme_light() +
                     scale_x_continuous(name="T/K") +
                     scale_y_continuous(name="DTG/s") +
                     ggtitle(r"DTG-T") +
                     theme(text=element_text(size=12, family="Times New Roman"),
                           plot_title=element_text(size=18))
                     )
        base_plot.save(f"./image/DTG-Fit-{method}.png", dpi=dpi, width=self.width, height=self.height)
        Logger.info(f"保存{method}-TG拟合数据")
        if show_fig:
            print(base_plot)

    def total_plot(self):
        self.plot_TG_DTG()
        self.plot_TG()
        self.plot_DTG()
        self.plot_fit_TG(method="hot")
        self.plot_fit_TG(method="burn")

    def correct_error(self, func, **kwargs):
        if kwargs:
            func(show_fig=True, **kwargs)
        else:
            func(show_fig=True)


if __name__ == '__main__':
    a = DataPloter(10, "test/ymt.txt")
    a.total_plot()