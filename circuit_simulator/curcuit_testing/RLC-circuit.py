from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('RLC Filter')
circuit.V('input', 'in_node', circuit.gnd, 5@u_V)  # AC幅值1V，相位0°
circuit.R("R", 'in_node', 'out', 10@u_Ohm)
circuit.L("L", 'out', 'mid', 10@u_mH)
circuit.C("C", 'mid', circuit.gnd, 1@u_uF)

simulator = circuit.simulator()
analysis = simulator.ac(start_frequency=10@u_Hz, stop_frequency=1@u_MHz, number_of_points=100, variation='dec')

# 获取复数输出（幅度和相位）
import numpy as np
vout_magnitude = np.array(analysis['out'])
vout_phase = np.angle(analysis['out'], deg=True)
#print("Output Voltage Magnitude (V):", vout_magnitude)
#print("Output Voltage Phase (degrees):", vout_phase)

simulator = circuit.simulator()
analysis = simulator.transient(step_time=0.01@u_ns, end_time=1@u_ns, start_time=0@u_ns)

# 查看时域波形
time = np.array(analysis.time)
vout = np.array(analysis['out'])
vmid = np.array(analysis['mid'])

for i in range(len(time)):
    print(f"Time: {time[i]} s, Vout: {vout[i] - vmid[i]} V")

# 输出到.csv文件
with open('output.csv', 'w') as f:
    for i in range(len(time)):
        f.write(f"{time[i]}, {vout[i] - vmid[i]}\n")