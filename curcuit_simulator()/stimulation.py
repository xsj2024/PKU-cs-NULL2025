from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction
from components import CircuitScene
from spice_generator import generate_spice_netlist

class CircuitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scene = CircuitScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        # 工具栏：添加元件
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        action_resistor = QAction("Resistor", self)
        action_resistor.triggered.connect(lambda: self.scene.add_component('R'))
        toolbar.addAction(action_resistor)
        
        # 仿真按钮
        action_simulate = QAction("Run SPICE", self)
        action_simulate.triggered.connect(self.run_simulation)
        toolbar.addAction(action_simulate)
    
    def run_simulation(self):
        circuit = generate_spice_netlist(self.scene)
        simulator = circuit.simulator()
        analysis = simulator.operating_point()  # 直流工作点分析
        print("Node Voltages:", {str(k): float(v) for k, v in analysis.items()})