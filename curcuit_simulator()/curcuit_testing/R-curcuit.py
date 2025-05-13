import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# 创建电路实例
circuit = Circuit('Resistor Network')

# 定义电源
circuit.V('input', 'in', circuit.gnd, 10)  # 10V电压源

# 串联电阻网络（R1和R2串联）
circuit.R(1, 'in', 'mid', 1000)  # R1=1kΩ
circuit.R(2, 'mid', 'out_series', 2000)  # R2=2kΩ

# 并联电阻网络（R3和R4并联，连接到串联网络的输出）
circuit.R(3, 'out_series', circuit.gnd, 3000)  # R3=3kΩ
circuit.R(4, 'out_series', circuit.gnd, 6000)  # R4=6kΩ

# 执行直流分析
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.operating_point()

# 提取节点电压和支路电流
print("===== 节点电压 =====")
for node in ('in', 'mid', 'out_series'):
    voltage = float(analysis[node])  # 转换为浮点数
    print(f"{node}: {voltage:.3f} V")

print("\n===== 支路电流 =====")
# 通过欧姆定律计算电流（I = V/R）
current_r1 = (float(analysis['in']) - float(analysis['mid'])) / 1e3  # R1电流
current_r2 = (float(analysis['mid']) - float(analysis['out_series'])) / 2e3  # R2电流
current_r3 = float(analysis['out_series'])  / 3e3  # R3电流
current_r4 = float(analysis['out_series']) / 6e3  # R4电流

print(f"R1电流: {current_r1 * 1e3:.3f} mA")
print(f"R2电流: {current_r2 * 1e3:.3f} mA")
print(f"R3电流: {current_r3 * 1e3:.3f} mA")
print(f"R4电流: {current_r4 * 1e3:.3f} mA")

# 理论计算验证
def parallel_resistance(r1, r2):
    return (r1 * r2) / (r1 + r2)

# 串联分压验证
total_series = 1e3 + 2e3  # R1 + R2
theory_mid = 10 * (2e3 / total_series)  # 理论分压值
print(f"\n理论分压 (mid节点): {theory_mid:.3f} V")

# 并联分流验证
parallel_r = parallel_resistance(3e3, 6e3)  # R3 || R4
total_current = float(analysis['out_series']) / (parallel_r + 0)  # 总电流（R3+R4路径）
theory_current_r4 = total_current * (3e3 / (3e3 + 6e3))  # 分流比例
print(f"理论分流 (R4电流): {theory_current_r4 * 1e3:.3f} mA")