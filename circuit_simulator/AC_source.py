from PyQt5.QtWidgets import QDoubleSpinBox
from ComponentItem import GraphicComponentItem
from components import PinItem

class ACSourceItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "V_AC")
        self.params = {
            "amplitude": 5.0,  # 幅值 (V)
            "frequency": 50,   # 频率 (Hz)
            "phase": 0         # 相位 (度)
        }
        
        # 专用参数编辑框
        self.param_editor = QDoubleSpinBox()
        self.param_editor.setRange(0.1, 1000)
        self.param_editor.setValue(50)
        self.param_editor.valueChanged.connect(self._update_freq)

    def _update_freq(self, value):
        self.params["frequency"] = value

    def spice_description(self):
        """生成SPICE网表描述"""
        return (f"SIN(0 {self.params['amplitude']} {self.params['frequency']} 0 0 {self.params['phase']})")
    

class OscilloscopeItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "OSC")
        self.waveforms = { "CH1": None, "CH2": None }
        self.setAcceptHoverEvents(True)
    