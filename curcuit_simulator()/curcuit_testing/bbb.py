import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('RC Circuit')
circuit.V('input', 1, circuit.gnd, 10)  # 10V电压源
circuit.R(1, 1, 2, 1)                 # 1kΩ电阻
circuit.C(1, 2, circuit.gnd, 1)       # 1μF电容

simulator = circuit.simulator()
analysis = simulator.transient(step_time=1@u_ms, end_time=10@u_ms)
print(analysis['2'])  # 输出节点2的电压