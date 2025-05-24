from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('RLC Filter')
circuit.V('input', 'in_node', circuit.gnd, 'DC 0 AC 1 SIN(0 1 1k 0 0 30)')  # AC幅值1V，相位0°
circuit.R("R", 'in_node', 'out', 1000@u_Ohm)
circuit.L("L", 'out', 'mid', 1@u_mH)
circuit.C("C", 'mid', circuit.gnd, 1@u_uF)

simulator = circuit.simulator()
analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=10@u_kHz, number_of_points=100, variation='dec')

# 获取复数输出（幅度和相位）
import numpy as np
vout_magnitude = np.array(analysis['out'])
vout_phase = np.angle(analysis['out'], deg=True)
print("Output Voltage Magnitude (V):", vout_magnitude)
print("Output Voltage Phase (degrees):", vout_phase)
# 画图
import matplotlib.pyplot as plt
frequencies = np.array(analysis.frequency)
plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(frequencies, 20 * np.log10(np.abs(vout_magnitude)), label='Magnitude (dB)')
plt.title('AC Analysis of RLC Circuit')

simulator = circuit.simulator()
analysis = simulator.transient(step_time=1@u_us, end_time=1000@u_us, start_time=0@u_ns)

# 查看时域波形
time = np.array(analysis.time)
vout = np.array(analysis['out'])
vmid = np.array(analysis['mid'])

for i in range(len(time)):
    print(f"Time: {time[i]} s, Vout: {vout[i] - vmid[i]} V")

# 画图
plt.subplot(2, 1, 2)
plt.plot(time, vout - vmid, label='Transient Response')
plt.xlabel('Time (s)')
plt.ylabel('Output Voltage (V)')
plt.grid()
plt.legend()
plt.show()

# 如果对circuit做直流分析，可能会报错
simulator = circuit.simulator()
analysis = simulator.dc(Vinput=slice(0, 10, 0.1))
# 获取直流输出
print("DC Analysis Output Voltage (V):", np.array(analysis['out']))