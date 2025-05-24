import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QToolBar, QAction, QVBoxLayout, QWidget
from stimulation import CircuitSimulator

if __name__ == "__main__":
    # 目前的代码需要改进的部分：
    # 1.wires不会跟随元件移动，直线太丑了
    # 2.UI界面不够美观
    # 3.没有完全实现电路连通性检查
    # 4.没有实现足够多的元件类型(补充了交流电路部分)
    # 5.没有实现仿真结果的可视化（例如电压表等）(partly fulfilled 除了示波器)
    # 6.pins的优化（例如接触提示和接触面积放大）
    # 7.没有实现网络的保存和加载
    # 8.运行spice与用户操作的分离
    # 9.撤回操作
    # 10.元件参数目前不可调节

    app = QApplication(sys.argv)
    window = CircuitSimulator()
    window.show()
    sys.exit(app.exec_())















