from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor, QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMainWindow, QAction, QToolBar
from PyQt5.QtGui import QBrush, QTransform
from spice_generator import generate_spice_netlist
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsSimpleTextItem

class PinItem(QGraphicsEllipseItem):
    def __init__(self, parent_component, pin_name, pos_x, pos_y):
        super().__init__(0, 0, 6, 6, parent=parent_component)  # 引脚为小圆点
        self.setPos(pos_x, pos_y)
        self.setBrush(QBrush(QColor(100, 100, 255)))  # 蓝色引脚
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.pin_name = pin_name  # 引脚名称（如 "left", "right"）
        self.parent_component = parent_component  # 所属元件
        self.connected_wires = []  # 存储连接的线
        self.node_name = None  # 节点名称
        self.voltage = None  # 电压值
        self.ac_voltage = None  # AC电压函数
        self.setAcceptHoverEvents(True)  # 接受悬停事件
        self.voltage_label = None  # 电压标签

    def mousePressEvent(self, event):
        # 点击引脚时触发连线逻辑
        if event.button() == Qt.LeftButton:
            self.scene().start_wire_from_pin(self)
        super().mousePressEvent(event)
    
    def set_voltage(self, voltage):
        """设置引脚电压值"""
        self.voltage = float(voltage) if voltage is not None else None
    
    def set_ac_voltage(self, ac_voltage):
        """设置交流电压函数"""
        if ac_voltage is not None:
            self.ac_voltage = ac_voltage
        else:
            self.ac_voltage = None

        
    def hoverEnterEvent(self, event):
        """鼠标悬停时显示电压"""
        if self.voltage is not None and self.voltage_label is None:
            # 创建电压标签
            self.voltage_label = QGraphicsSimpleTextItem(f"{self.voltage:.2f}V", self)
            self.voltage_label.setPos(self.x() + 10, self.y() - 20)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """鼠标移出时移除电压标签"""
        if (self.voltage is not None) and self.voltage_label is not None:
            self.scene().removeItem(self.voltage_label)
            self.voltage_label = None
        super().hoverLeaveEvent(event)

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
        elif spice_type == 'D':
            self.pins['anode'] = PinItem(self, "anode", 0, self.rect().height()/2)
            self.pins['cathode'] = PinItem(self, "cathode", self.rect().width(), self.rect().height()/2)


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
