from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction
from spice_generator import generate_spice_netlist
from components import ComponentItem, PinItem, WireItem, CircuitScene
from ComponentItem import GraphicComponentItem
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QListWidget, 
    QToolBar, QTabWidget, QWidget, QVBoxLayout, QPushButton
)
import sys
from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QToolBar, QAction, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QBrush, QTransform


class CircuitSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt + PySpice 电路模拟器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建左侧元件停靠窗口
        self._create_component_dock()

        # 初始化场景和视图
        self.scene = CircuitScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)  # 启用抗锯齿
        self.view.setRenderHint(QPainter.TextAntialiasing)  # 文本抗锯齿
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 主布局
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 状态栏显示操作提示
        self.statusBar().showMessage("拖放元件并连线，点击仿真运行SPICE")

    def _create_component_dock(self):
        """创建左侧元件列表停靠栏"""
        dock = QDockWidget("元件库", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        
        # 使用选项卡分类元件
        tab_widget = QTabWidget()

        # 基础元件选项卡
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        self._add_component_buttons(basic_layout, ["电阻", "电容", "电压源", "接地"])
        basic_tab.setLayout(basic_layout)
        
        # 半导体选项卡（未来扩展）
        semi_tab = QWidget()
        semi_layout = QVBoxLayout()
        self._add_component_buttons(semi_layout, ["二极管", "晶体管"])
        semi_tab.setLayout(semi_layout)
        
        tab_widget.addTab(basic_tab, "基础元件")
        tab_widget.addTab(semi_tab, "半导体")
        
        dock.setWidget(tab_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    
    def _add_component_buttons(self, layout, components, enabled=True):
        """动态添加元件按钮到布局"""
        for comp in components:
            btn = QPushButton(comp)
            btn.setEnabled(enabled)
            btn.clicked.connect(lambda _, c=comp: self._add_component(c))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px;
                    font-size: 14px;
                    text-align: left;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #f0f0f0;
                }
            """)
            layout.addWidget(btn)
        layout.addStretch()  # 添加弹性空间

    def _create_toolbar(self):
        """创建工具栏按钮"""
        toolbar = QToolBar("元件")
        self.addToolBar(toolbar)
        
        # 添加电阻
        action_resistor = QAction("电阻", self)
        action_resistor.triggered.connect(lambda: self._add_component("R"))
        toolbar.addAction(action_resistor)
        
        # 添加电压源
        action_voltage = QAction("电压源", self)
        action_voltage.triggered.connect(lambda: self._add_component("V"))
        toolbar.addAction(action_voltage)
        
        action_gnd = QAction("接地", self)
        action_gnd.triggered.connect(lambda: self._add_component("GND"))
        toolbar.addAction(action_gnd)
        
        # 添加仿真按钮
        action_simulate = QAction("运行SPICE", self)
        action_simulate.triggered.connect(self._run_spice_simulation)
        toolbar.addAction(action_simulate)
        
        # 添加清除按钮
        action_clear = QAction("清除", self)
        action_clear.triggered.connect(self._clear_scene)
        toolbar.addAction(action_clear)

    def _add_component(self, component_type):
        """向场景中添加元件"""
        if component_type == "R" or component_type == "电阻":
            item = GraphicComponentItem(f"R{len(self.scene.components) + 1}", "R")
        elif component_type == "V" or component_type == "电压源":
            item = GraphicComponentItem(f"V{len(self.scene.components) + 1}", "V")
        elif component_type == "GND" or component_type == "接地":
            item = GraphicComponentItem(f"GND{len(self.scene.components) + 1}", "GND")
        elif component_type == "二极管" or component_type == "D":
            item = GraphicComponentItem(f"D{len(self.scene.components) + 1}", "D")

        self.scene.addItem(item)
        self.scene.components.append(item)
        self.statusBar().showMessage(f"已添加 {item.name}")

    def _run_spice_simulation(self):
        """生成SPICE网表并调用PySpice"""
        #try:
        from PySpice.Spice.Netlist import Circuit
            
            # 直接调用generate_spice_netlist函数
        circuit = generate_spice_netlist(self.scene)

            # 打印网表（实际可调用PySpice仿真）
        print("生成的SPICE网表:")
        print(circuit)
            
            # 模拟操作（示例：直流工作点分析）
        simulator = circuit.simulator()
        analysis = simulator.operating_point()
        print("仿真成功！结果如下：")
        for node in analysis.nodes.values():
            print(f"Node {str(node)}: {float(node):.3f} V")
            # 更新所有引脚的电压值
        dict = analysis.nodes
        for comp in self.scene.components:
            for pin_name, pin_item in comp.pins.items():
                    # 先将引脚电压设为None
                pin_item.set_voltage(None)
                # 获取引脚对应的SPICE节点名
                node_name = pin_item.node_name
                if node_name in dict:
                    # 设置引脚电压
                    pin_item.set_voltage(dict[node_name])
                elif node_name == '0':
                    # 如果是接地引脚，设置电压为0
                    pin_item.set_voltage(0.0)

                    
        
        #except ImportError:
        #    QMessageBox.critical(self, "错误", "未安装PySpice！请运行: conda install -c conda-forge PySpice==1.5")
        #except Exception as e:
        #    QMessageBox.critical(self, "错误", f"仿真失败: {str(e)}")
        #    print("仿真失败:", str(e))
        #    # 显示原始SPICE输出以调试
        #    if hasattr(simulator, 'stdout'):
        #        print("SPICE输出:", simulator.stdout)

    def _clear_scene(self):
        """清空场景"""
        self.scene.clear()
        self.scene.components = []
        self.scene.wires = []
        self.statusBar().showMessage("场景已清除")