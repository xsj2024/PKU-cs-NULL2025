from PyQt5.QtWidgets import QDoubleSpinBox
from Components.ComponentItem import GraphicComponentItem
from Components.components import PinItem

class ACSourceItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "V_AC")
        self.params.update({
            "amplitude": 5.0,  # 幅值 (V)
            "frequency": 50,   # 频率 (Hz)
            "phase": 0         # 相位 (度)
        })

    def _update_freq(self, value):
        self.params["frequency"] = value

    def spice_description(self):
        """生成SPICE网表描述"""
        return (f"SIN(0 {self.params['amplitude']} {self.params['frequency']} 0 0 {self.params['phase']})")
    

class OscilloscopeItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "OSC")
        self.setAcceptHoverEvents(True)

        self.params.update({
            "time_range": 1.0,  # 时间范围 (s)
            "channels":{"CH1": 0, "CH2": 0},  # 通道设置
            "mode": "DC"  # 示波器模式
        })
    