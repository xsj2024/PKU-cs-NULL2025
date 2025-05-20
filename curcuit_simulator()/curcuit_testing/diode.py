from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# 创建电路实例
circuit = Circuit('Diode Test')

# 1. 定义二极管模型（必须！）
circuit.model('MyDiode', 'D', IS=1e-14)  # 注意模型名拼写一致性

# 2. 添加电源和电阻
circuit.V('input', 'input_node', circuit.gnd, 5@u_V)  # 5V电源
circuit.R(1, 'input_node', 'diode_anode', 1@u_kOhm)  # 限流电阻

# 3. 正确接入二极管（节点名用字符串）
circuit.D('D1','diode_anode','diode_cathode',model = "MyDiode")  # 阳极→阴极
circuit.R(2, 'diode_cathode', circuit.gnd, 2@u_kOhm)       # 负载电阻

# 执行仿真
simulator = circuit.simulator()
analysis = simulator.operating_point()
print(f"Diode Voltage: {float(analysis['diode_anode'].item() - float(analysis['diode_cathode'].item())):.3f} V")