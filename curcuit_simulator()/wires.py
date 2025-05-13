from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsScene
from PyQt5.QtGui import QPainterPath
from PyQt5.QtGui import QPen, QColor

class WireItem(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin):
        super().__init__()
        self.start_pin = start_pin  # 起始引脚
        self.end_pin = end_pin      # 结束引脚
        self.update_path()
        
    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pin.scenePos())
        path.lineTo(self.end_pin.scenePos())
        self.setPath(path)
        self.setPen(QPen(QColor(0, 0, 0), 2))

