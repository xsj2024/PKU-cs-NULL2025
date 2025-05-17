from PySpice.Spice.Simulation import CircuitSimulation , CircuitSimulator
from PySpice.Logging import Logging
import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()
import PySpice
from PySpice.Spice.Library import SpiceLibrary


from PySpice.Spice.Netlist import Circuit, SubCircuit, SubCircuitFactory
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
from PySpice.Doc.ExampleTools import find_libraries
libraries_path = find_libraries()
spice_library = SpiceLibrary(libraries_path)
print("SPICE库路径:", libraries_path)
# 测试电路
circuit = Circuit('Test')
#circuit.include(spice_library['d1n5919brl'])
circuit.V('input', '1', circuit.gnd, 10)
circuit.R('R1', '2', circuit.gnd, 1e3)
circuit.C('C1', '1', '2', 10)
#circuit.model('MyDiode', 'D', IS=1e-14)  # 定义模型
#circuit.D('1', '1', '2', 'MyDiode')
simulator = circuit.simulator()
analysis = simulator.operating_point()
print("节点电压:", float(analysis['2'].item()))