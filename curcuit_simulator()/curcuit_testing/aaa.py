from PySpice.Spice.Simulation import CircuitSimulation , CircuitSimulator
from PySpice.Logging import Logging
import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()
import PySpice
from PySpice.Spice.Library import SpiceLibrary


from PySpice.Spice.Netlist import Circuit, SubCircuit, SubCircuitFactory
from PySpice.Unit import *

# 测试电路
circuit = Circuit('Test')
circuit.V('input', 1, circuit.gnd, 10)
circuit.R(1, 1, circuit.gnd, 1e3)

simulator = circuit.simulator()
analysis = simulator.operating_point()
print("节点电压:", float(analysis['1']))