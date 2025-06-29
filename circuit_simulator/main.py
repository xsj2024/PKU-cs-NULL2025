import sys
from PyQt5.QtWidgets import QApplication
from stimulation import CircuitSimulator

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CircuitSimulator()
    window.show()
    sys.exit(app.exec_())

