2025上半年北京大学程序设计实习大作业NULL组

队内成员：谢尚杰，王玺傲，刘子豪。

主要内容：基于PySpice,PyQt5和ngspice的电路可视化程序

# 目前可用的元件类型：

基础元件：电阻R（默认阻值1000欧），电压源V（默认电压5伏），接地元件GND

非线性元件：二极管D（默认特征电流Is为1e-14安培）

交流元件：电容C（默认电容值为1微法），电感L（默认电感值为1毫亨），交流源（目前只支持正弦波形和方波波形）

# 代码结构：

## main.py：

启用主窗口

## stimulation.py：

定义主窗口CircuitSimulator(QMainWindow)

## components.py：

实现基础元件类ComponentItem(QGraphicsRectItem)，引脚类PinItem(QGraphicsEllipseItem)，以及可以基于鼠标互动实现引脚连接的CircuitScene(QGraphicsScene)类

## ComponentItem.py：

实现视图元件类GraphicComponentItem(QGraphicsPixmapItem)，结构与ComponentItem类似

## spice_generator.py：

定义两个函数：对给定的CircuitScene对象，给出符合Spice语法的Spice网表的函数generate_spice_netlist(scene)；以及根据CircuitScene对象检查电路性质的函数validate_connections(scene)。

## icons：

保存用于GraphicComponentItem视图的.png文件

## AC_source.py：

在视图元件类GraphicComponentItem基础上派生两个元件类ACSourceItem和OscilloscopeItem，提供对交流电路分析的支持。

另外还定义了OscilloscopeWindow(QMainWindow)，用于显示波形

## basic.py：

在视图元件类GraphicComponentItem基础上派生了其他基础元件的元件类，规范了元件参数的格式。

## shortcuts_manager.py：

管理快捷键功能

## files_manager.py

文件打开、保存、创建等功能

## command_manager.py

统一管理模拟器的操作，操作包括：
添加元件
删除元件
添加连线
删除连线
清空场景

## parameter_editor.py：

定义了一个编辑元件参数的侧面窗口ParameterEditorDock(QDockWidget)

# 必要的库的安装：

建议使用anaconda

## 在conda中运行如下指令：

conda create --name pyspice python=3.9.21

conda activate pyspice

conda install conda-forge pyspice=1.5

conda install numpy

conda install pandas

pip install pyqt5

## 结束使用后运行：

conda deactivate

