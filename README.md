2025上半年北京大学程序设计实习大作业NULL组

队内成员：谢尚杰，王玺傲，刘子豪。

主要内容：基于PySpice,PyQt5和ngspice的电路可视化程序

目前可用的元件类型：
基础元件：电阻R（默认阻值1000欧），电压源V（默认电压5伏），接地元件GND
非线性元件：二极管D（默认特征电流Is为1e-14安培）

代码结构：

main.py：启用主窗口

stimulation.py：定义主窗口CircuitSimulator(QMainWindow)

wires.py：基于QGraphicsPathItem，初步实现在引脚PinItem之间连线的类WireItem的定义

components.py：实现元件类ComponentItem(QGraphicsRectItem)，引脚类PinItem(QGraphicsEllipseItem)，以及可以基于鼠标互动实现引脚连接的CircuitScene(QGraphicsScene)类

ComponentItem.py：实现视图元件类GraphicComponentItem(QGraphicsPixmapItem)，结构与ComponentItem类似

spice_generator.py：定义两个函数：对给定的CircuitScene对象，给出符合Spice语法的Spice网表的函数generate_spice_netlist(scene)；以及根据CircuitScene对象检查电路性质的函数validate_connections(scene)。

icons：保存用于GraphicComponentItem视图的.png文件