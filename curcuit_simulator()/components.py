from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMainWindow, QAction, QToolBar
from PyQt5.QtGui import QBrush, QTransform
from wires import WireItem
from spice_generator import generate_spice_netlist
from PyQt5.QtWidgets import QGraphicsLineItem

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

class PinItem(QGraphicsEllipseItem):
    def __init__(self, parent_component, pin_name, pos_x, pos_y):
        super().__init__(0, 0, 6, 6, parent=parent_component)  # 引脚为小圆点
        self.setPos(pos_x, pos_y)
        self.setBrush(QBrush(QColor(100, 100, 255)))  # 蓝色引脚
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.pin_name = pin_name  # 引脚名称（如 "left", "right"）
        self.parent_component = parent_component  # 所属元件
        self.connected_wires = []  # 存储连接的线

    def mousePressEvent(self, event):
        # 点击引脚时触发连线逻辑
        if event.button() == Qt.LeftButton:
            self.scene().start_wire_from_pin(self)
        super().mousePressEvent(event)

class ComponentItem(QGraphicsRectItem):
    def __init__(self, name, spice_type):
        super().__init__(0, 0, 50, 30)
        self.name = name
        self.spice_type = spice_type
        self.pins = {}  # 字典存储
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        if spice_type == 'R':
            self.pins['left'] = PinItem(self, "left", 0, self.rect().height()/2)
            self.pins['right'] = PinItem(self, "right", self.rect().width(), self.rect().height()/2)
        elif spice_type == 'V':
            self.pins['plus'] = PinItem(self, "plus", self.rect().width()/2, 0)
            self.pins['minus'] = PinItem(self, "minus", self.rect().width()/2, self.rect().height())
        elif spice_type == 'GND':
            self.pins['gnd'] = PinItem(self, "gnd", self.rect().width()/2, self.rect().height())


    def paint(self, painter, option, widget):
        # 绘制元件矩形
        painter.drawRect(self.rect())
        # 引脚由PinItem自行绘制，无需在此处理

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for pin in self.pins.values():
                for wire in pin.connected_wires:
                    wire.update_path()
        return super().itemChange(change, value)

class CircuitScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.components = []
        self.wires = []
        self.temp_wire = None  # 临时连线（鼠标拖动时显示）

    def start_wire_from_pin(self, pin):
        # 开始从引脚拖动连线
        self.temp_start_pin = pin
        self.temp_wire = None  # 清除之前的临时连线
        self.temp_wire = QGraphicsLineItem(
            pin.scenePos().x(), pin.scenePos().y(),
            pin.scenePos().x(), pin.scenePos().y()
        )
        self.temp_wire.setPen(QPen(Qt.blue, 2))
        self.addItem(self.temp_wire)

    def mouseMoveEvent(self, event):
        # 更新临时连线终点
        if hasattr(self, 'temp_wire'):
            if self.temp_wire:
                start_pos = self.temp_wire.line().p1()
                self.temp_wire.setLine(
                    start_pos.x(), start_pos.y(),
                    event.scenePos().x(), event.scenePos().y()
                )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'temp_start_pin'):
            # 获取所有在释放位置的项（而不仅是顶层项）
            items = self.items(event.scenePos())
            end_pin = None
            for item in items:
                if isinstance(item, PinItem) and item != self.temp_start_pin:
                    end_pin = item
                    break
        
            if end_pin:  # 找到有效引脚
                print("Connecting wires")
                wire = WireItem(self.temp_start_pin, end_pin)
                self.addItem(wire)
                self.wires.append(wire)
            else:
                print("No valid end pin found")
        
            # 清理临时项
            self.removeItem(self.temp_wire)
            del self.temp_wire
            del self.temp_start_pin
        super().mouseReleaseEvent(event)
