from Components.ComponentItem import GraphicComponentItem


class ResistorItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "R")
        self.params = {
            "resistance": 1000,  # 电阻值 (Ohm)
        }
        self.setAcceptHoverEvents(True)

    def set_param(self, param_name, value):
        """设置参数值"""
        if param_name in self.params:
            # 检查值的范围
            if param_name == "resistance":
                if value < 0:
                    print("电阻值不能为负数!")
                else:
                    self.params[param_name] = value
        else:
            raise ValueError(f"Parameter {param_name} not found in {self.name}")

    def spice_description(self):
        """生成SPICE网表描述"""
        return f"{self.name} {self.pins['left'].node_name} {self.pins['right'].node_name} {self.params['resistance']}"
    
class CapacitorItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "C")
        self.params = {
            "capacitance": 1e-6,  # 电容值 (F)
        }
        self.setAcceptHoverEvents(True)

    def spice_description(self):
        """生成SPICE网表描述"""
        return f"{self.name} {self.pins['left'].node_name} {self.pins['right'].node_name} {self.params['capacitance']}"

class InductorItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "L")
        self.params = {
            "inductance": 1e-3,  # 电感值 (H)
        }
        self.setAcceptHoverEvents(True)

    def spice_description(self):
        """生成SPICE网表描述"""
        return f"{self.name} {self.pins['left'].node_name} {self.pins['right'].node_name} {self.params['inductance']}"

class VoltageSourceItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "V")
        self.params = {
            "voltage": 5.0,  # 电压值 (V)
        }
        self.setAcceptHoverEvents(True)

    def spice_description(self):
        """生成SPICE网表描述"""
        return f"{self.name} {self.pins['plus'].node_name} {self.pins['minus'].node_name} {self.params['voltage']}"

class GroundItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "GND")
        self.setAcceptHoverEvents(True)

    def spice_description(self):
        """生成SPICE网表描述"""
        # 地线不需要显式地在网表中描述
        return ""
    
class DiodeItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "D")
        self.params = {
            "Is": 1e-12,  # 饱和电流 (A)
        }
        self.setAcceptHoverEvents(True)

    def spice_description(self):
        """生成SPICE网表描述"""
        # 由于二极管需要预先定义模型，所以正常运行时这里不会被调用
        raise NotImplementedError("Diode model not implemented in SPICE.")


