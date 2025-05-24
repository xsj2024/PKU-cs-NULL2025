from PyQt5.QtWidgets import QDockWidget, QWidget, QFormLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt

class ParameterEditorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("参数编辑器", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        
        # 主容器
        self.container = QWidget()
        self.layout = QFormLayout()
        self.container.setLayout(self.layout)
        self.setWidget(self.container)
        
        # 当前编辑的元件
        self.current_item = None

    def clear(self):
        """清空当前编辑界面"""
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().deleteLater()

    def edit_component(self, component):
        self.clear()
        self.current_item = component
        
        # 通用参数
        self._add_generic_parameters(component)
        
        # 类型特定参数
        self._add_type_specific_parameters(component)

    def _add_generic_parameters(self, component):
        """添加名称和基础参数"""
        name_edit = QLineEdit(component.name)
        name_edit.textChanged.connect(lambda v: setattr(component, 'name', v))
        self.layout.addRow("名称", name_edit)

    def _add_type_specific_parameters(self, component):
        """根据元件类型添加特定参数"""
        if component.spice_type == "R":
            self._add_resistor_parameters(component)
        elif component.spice_type == "C":
            self._add_capacitor_parameters(component)
        elif component.spice_type == "L":
            self._add_inductor_parameters(component)
        elif component.spice_type == "V":
            self._add_voltage_source_parameters(component)
        elif component.spice_type == "V_AC":
            self._add_ac_source_parameters(component)
        elif component.spice_type == "OSC":
            self._add_oscilloscope_parameters(component)
        elif component.spice_type == "D":
            self._add_diode_parameters(component)
        # 其他元件类型可以在这里添加
        

    # 下面具体地实现每种元件类型的参数编辑
    def _add_resistor_parameters(self, component):
        """添加电阻特定参数"""
        resistance_edit = QDoubleSpinBox()
        resistance_edit.setRange(0.1, 1000000)
        resistance_edit.setValue(component.params["resistance"])
        # 将信号连接到component的字典params
        resistance_edit.valueChanged.connect(lambda v: component.set_param("resistance", v))
        
        self.layout.addRow("电阻值 (Ω)", resistance_edit)
    
    def _add_capacitor_parameters(self, component):
        """添加电容特定参数"""
        capacitance_edit = QDoubleSpinBox()
        capacitance_edit.setRange(0.1, 1000000)
        capacitance_edit.setValue(component.params["capacitance"])
        capacitance_edit.valueChanged.connect(lambda v: component.set_param("capacitance", v))
        
        self.layout.addRow("电容值 (F)", capacitance_edit)
    
    def _add_inductor_parameters(self, component):
        """添加电感特定参数"""
        inductance_edit = QDoubleSpinBox()
        inductance_edit.setRange(0.1, 1000000)
        inductance_edit.setValue(component.params["inductance"])
        inductance_edit.valueChanged.connect(lambda v: component.set_param("inductance", v))
        
        self.layout.addRow("电感值 (H)", inductance_edit)
    
    def _add_voltage_source_parameters(self, component):
        """添加电压源特定参数"""
        voltage_edit = QDoubleSpinBox()
        voltage_edit.setRange(-1000, 1000)
        voltage_edit.setValue(component.params["voltage"])
        voltage_edit.valueChanged.connect(lambda v: component.set_param("voltage", v))
        
        self.layout.addRow("电压值 (V)", voltage_edit)

    def _add_ac_source_parameters(self, component):
        """添加交流源特定参数"""
        amplitude_edit = QDoubleSpinBox()
        amplitude_edit.setRange(0.1, 1000)
        amplitude_edit.setValue(component.params["amplitude"])
        amplitude_edit.valueChanged.connect(lambda v: component.set_param("amplitude", v))
        
        frequency_edit = QDoubleSpinBox()
        frequency_edit.setRange(0.1, 100000)
        frequency_edit.setValue(component.params["frequency"])
        frequency_edit.valueChanged.connect(lambda v: component.set_param("frequency", v))
        
        phase_edit = QDoubleSpinBox()
        phase_edit.setRange(-360, 360)
        phase_edit.setValue(component.params["phase"])
        phase_edit.valueChanged.connect(lambda v: component.set_param("phase", v))
        
        self.layout.addRow("幅值 (V)", amplitude_edit)
        self.layout.addRow("频率 (Hz)", frequency_edit)
        self.layout.addRow("相位 (°)", phase_edit)

    def _add_oscilloscope_parameters(self, component):
        """添加示波器特定参数"""
        # 这里可以添加示波器的特定参数编辑
        # 例如，时间范围、触发电平等
        time_range_edit = QDoubleSpinBox()
        time_range_edit.setRange(0.1, 1000)
        time_range_edit.setValue(component.params["time_range"])
        time_range_edit.valueChanged.connect(lambda v: component.set_param("time_range", v))

        self.layout.addRow("时间范围 (s)", time_range_edit)

    def _add_diode_parameters(self, component):
        """添加二极管特定参数"""
        Is_edit = QDoubleSpinBox()
        Is_edit.setRange(0.1, 1000)
        Is_edit.setValue(component.params["Is"])
        Is_edit.valueChanged.connect(lambda v: component.set_param("Is", v))

        self.layout.addRow("饱和电流 (A)", Is_edit)

    # 其余元件类型的参数编辑方法可以在这里添加
        
