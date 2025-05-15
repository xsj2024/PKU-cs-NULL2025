import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QToolBar, QAction, QVBoxLayout, QWidget
from stimulation import CircuitSimulator

if __name__ == "__main__":
    # 目前的代码需要改进的部分：
    # 1.wires不会跟随元件移动
    # 2.UI界面不够美观
    # 3.没有完全实现电路连通性检查
    # 4.没有实现足够多的元件类型
    # 5.没有实现仿真结果的可视化（例如电压表等）

    app = QApplication(sys.argv)
    window = CircuitSimulator()
    window.show()
    sys.exit(app.exec_())















