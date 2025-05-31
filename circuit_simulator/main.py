import sys
from PyQt5.QtWidgets import QApplication
from stimulation import CircuitSimulator

if __name__ == "__main__":
# 目前的代码需要改进的部分：
    # 1.wires外形的优化
    # 2.UI界面美化
    # 3.没有实现网络的保存和加载 (已完成)
    # 4.运行spice与用户操作的分离
    # 5.撤回操作 (已完成)
    # 6.示波器功能完善

    app = QApplication(sys.argv)
    window = CircuitSimulator()
    window.show()
    sys.exit(app.exec_())






