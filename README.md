2025上半年北京大学程序设计实习大作业NULL组

队内成员：谢尚杰，王玺傲，刘子豪。

主要内容：基于PySpice,PyQt5和ngspice的电路可视化程序

代码结构：

main.py：定义主窗口CircuitSimulator(QMainWindow)，并启用之

stimulation.py：并没有用到的另一个主窗口程序部分

wires.py：基于QGraphicsPathItem，初步实现在引脚PinItem之间连线的类WireItem的定义

components.py：实现元件类ComponentItem(QGraphicsRectItem)，引脚类PinItem(QGraphicsEllipseItem)，以及可以基于鼠标互动实现引脚连接的CircuitScene(QGraphicsScene)类

spice_generator.py：定义两个函数：对给定的CircuitScene对象，给出符合Spice语法的Spice网表的函数generate_spice_netlist(scene)；以及根据CircuitScene对象检查电路性质的函数validate_connections(scene)。
