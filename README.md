# TGAreporter—自动生成xjtu热重实验图片

能动B2104 杨牧天

完整脚本参见：[https://github.com/proletarianwarrior/TGAreporter](https://github.com/proletarianwarrior/TGAreporter)

## 快速开始

1. 将实验数据的`txt`文件放置在`./test`文件夹下
2. 生成绘图器实例`DataPloter`

```python
a = DataPloter(10, "data/data.txt")
```

> 第一个参数为`w0`为所用样品的重量，单位为`mg`
>
> 第二个参数为文件路径，接受`str`和`pythlib`的内置类型`Path`

3. 使用绘图方法`total_plot`

```python
a.total_plot()
```

4. 运行脚本
5. 检查数据导入和数据解析是否正确

<img src=".\picture\0.png" style="zoom: 25%;" />

6. 根据弹出的特征点图片检查特征点位置是否合理（可通过绘图窗口的缩放工具查看细节）

<img src=".\picture\1.png">

<img src=".\picture\2.png" style="zoom:50%;" />

> 例如：修改max_x2的横坐标，只需输入max_x2，接着输入要更改的值即可完成更改，更改结果如下（**输入N或n表示更改结束**）：

<img src=".\picture\3.png" style="zoom:50%;" />

7. 等待程序运行完毕，在`./picture`目录下查看绘制的图片



## 高级用法

该脚本提供了一些更加高级的用法，如下：

### 设置滤波方式

对于不同的数据，不同的滤波方式会使数据处理结果带来差异，本脚本可选择的滤波方式有两种，分别为**惯性滤波**和**高斯低通滤波**

使用方式如下：

```python
a = DataPloter(10, "data/data.txt", filter_method="butter", N=2, Wn=0.03)
```

> 参数`filter_method`可选择`butter`、`inertial`分别是高斯低通滤波和惯性滤波
>
> 当选择惯性滤波时可传入惯性系数`a`，默认值为0.03
>
> 当选择高斯低通滤波时可传入阶数`N`和截止频率`Wn`。一般来讲，较低的`N`值和`Wn`值可以使曲线更加平滑。默认值为`N=10`，`Wn=0.1`
>
> **默认使用惯性滤波**

### 设置特征值算法参数

**如非特殊需要（特殊需要例如数据无法手动选择或者想要使特征点的选择更具科学性），无需修改本节涉及的参数**

为了更合理的寻找特征点，本脚本设定了两个函数对特征点进行搜寻

1. `find_typical_minima`（寻找典型最小值）

该函数接受四个参数，参数说明如下：

|   `data`    | 一维数组（一般是滤波后的部分DTG数据） | nan  |
| :---------: | :-----------------------------------: | ---- |
|     `n`     |           典型最小值的个数            | 1    |
| `tolerance` |             最大容错个数              | 1    |
| `min_down`  |          双边最小上升点个数           | 10   |

**该函数实现如下逻辑：**在`data`中遍历寻找所有极值点位置（该点的数值低于相邻两点），遍历所有极值点；对于每个极值点，分别搜索其左右两侧连续上升点的个数，其中如有不超过`tolerance`的点呈下降趋势则继续搜寻，忽略该“错误”；如果该极值点的左右两侧的连续上升点个数均大于`min_down`，则判定该点为典型最小值点，并将左右两侧连续上升点加和作为其分数；最终选取分数为前`n`的典型最小值点作为返回值。

2. `find_first_stable_point`  (找出在给定窗口大小内变化低于阈值的第一个数据点。)

该函数接受四个参数，参数说明如下：

|    `data`     | 一维数组（一般是滤波后的部分DTG数据） | nan  |
| :-----------: | :-----------------------------------: | ---- |
| `window_size` |               窗口大小                | 500  |
|  `threshold`  | 将数据视为稳定数据的最大允许变化量。  | 1e-5 |
|  `del_size`   |          允许的最大离群个数           | 50   |

**该函数实现如下逻辑：**在`data`中 按顺序遍历每个数据点；对于每个数据点，查看其后方大小为`window_size`的点，计算每个点与该数据点的差值是否大于`threshold`，大于`threshold`的点称为离群点，找到第一个离群点总个数不大于`del_size`的数据点位置作为返回值

### 设置绘图纠错

为了防止绘制的图像结果达不到预期，可以对绘制的图像进行纠错处理。

操作方法如下：

1. 调用`correct_error`方法

```python
a.correct_error(a.plot_fit_TG, method="hot")
```

> 该方法使用绘图函数作为形参，如果该函数有接受的参数，可将该参数的参数向后写入

**该方法主要应用于动力区间的拟合**

如果对动力区间的选取不满意，可以传入参数`Tlim`，该参数为元组形式的**温度区间（摄氏度）**，示例如下：

```python
a.correct_error(a.plot_fit_TG, method="hot", Tlim=(230, 350))
```

## 绘图风格展示T

1. `TG-T`图像

<img src=".\picture\TG.png">

2. `DTG-T`图像

<img src=".\picture\DTG.png">

3. `DTG-TG-T`图像

<img src=".\picture\DTG-TG.png">

4. `DTG-Fit-T-hot`图像

<img src=".\picture\DTG-Fit-hot.png">

5. `DTG-Fit-T-burn`图像

<img src=".\picture\DTG-Fit-burn.png">