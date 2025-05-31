from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor, QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMainWindow, QAction, QToolBar
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import QPointF, pyqtSignal, QObject

class PinProxy(QObject):
    """代理类，用于处理引脚的信号和槽"""
    position_changed = pyqtSignal()  # 位置变化信号

class PinItem(QGraphicsEllipseItem):
    def __init__(self, parent_component, pin_name, pos_x, pos_y):
        super().__init__(-4, -4, 8, 8, parent=parent_component)  # 引脚为小圆点
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
        self.proxy = PinProxy()  # 创建代理类实例
        self.posChanged = self.proxy.position_changed  # 位置变化信号
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)

    def itemChange(self, change, value):
        if change == 27:  # ItemPositionChange
            self.proxy.position_changed.emit()
        return super().itemChange(change, value)

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
        # 外观设为高亮
        self.setBrush(QBrush(QColor(255, 100, 100)))  # 高亮显示
        if self.voltage is not None and self.voltage_label is None:
            # 创建电压标签
            self.voltage_label = QGraphicsSimpleTextItem(f"{self.voltage:.2f}V", self)
            self.voltage_label.setPos(self.x() + 10, self.y() - 20)
        # 通知Scene更新显示
        if self.scene():
            self.scene().pin_hover(self, True)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """鼠标移出时移除电压标签"""
        # 恢复外观
        self.setBrush(QBrush(QColor(100, 100, 255)))  # 恢复原色
        if (self.voltage is not None) and self.voltage_label is not None:
            self.scene().removeItem(self.voltage_label)
            self.voltage_label = None
        # 通知Scene更新显示
        if self.scene():
            self.scene().pin_hover(self, False)
        super().hoverLeaveEvent(event)

    def add_wire(self, wire):
        if wire not in self.connected_wires:
            self.connected_wires.append(wire)

    def remove_wire(self, wire):
        if wire in self.connected_wires:
            self.connected_wires.remove(wire)


class CircuitScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__()
        self.components = []
        self.wires = []
        self.temp_wire = None  # 临时连线（鼠标拖动时显示）
        self.main_window = parent  # 保存主窗口引用

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
                # 使用命令管理器添加连线
                if self.main_window and hasattr(self.main_window, 'command_manager'):
                    self.main_window.add_wire_with_command(wire)
                else:
                    # 备用方案：直接添加
                    self.addItem(wire)
                    self.wires.append(wire)
            else:
                print("No valid end pin found")
        
            # 清理临时项
            if hasattr(self, 'temp_wire'):
                self.removeItem(self.temp_wire)
                del self.temp_wire
            del self.temp_start_pin
        super().mouseReleaseEvent(event)

    def pin_hover(self, pin, is_hovered):
        """处理引脚悬停事件"""
        if is_hovered:
            if pin.voltage is not None:
                self.main_window.voltage_label.setText(f"Voltage at {pin.pin_name}: {pin.voltage:.2f} V")
            else:
                self.main_window.voltage_label.setText(f"Voltage at {pin.pin_name}: N/A")
        else:
            self.main_window.voltage_label.setText("")

    def _find_end_pin(self, pos):
        for item in self.items(pos):
            if isinstance(item, PinItem) and item != self.temp_start_pin:
                return item
        print("No valid end pin found at position:", pos)
        return None

    def _finalize_wire(self, wire):
        self.addItem(wire)
        self.wires.append(wire)
        wire.start_pin.add_wire(wire)
        wire.end_pin.add_wire(wire)

    def _cleanup_temp_items(self):
        self.removeItem(self.temp_wire)
        del self.temp_wire
        del self.temp_start_pin

from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsScene
from PyQt5.QtGui import QPainterPath
from PyQt5.QtGui import QPen, QColor

class WireItem(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setZValue(1)  # 确保导线在元件上方显示
        
        # 连接信号以动态更新路径
        self.start_pin.proxy.position_changed.connect(self.update_path)
        self.end_pin.proxy.position_changed.connect(self.update_path)
        
        self.update_path()

    def update_path(self):
        """生成平滑的导线路径（贝塞尔曲线或智能折线）"""
        start_pos = self.start_pin.scenePos()
        end_pos = self.end_pin.scenePos()
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # 根据引脚相对位置选择路径类型
        if self._should_use_straight_line():
            path.lineTo(end_pos)  # 直线连接
        else:
            # 贝塞尔曲线（控制点为中间点偏移）
            ctrl1 = QPointF(
                start_pos.x() + (end_pos.x() - start_pos.x()) * 0.5,
                start_pos.y()
            )
            ctrl2 = QPointF(
                end_pos.x() - (end_pos.x() - start_pos.x()) * 0.5,
                end_pos.y()
            )
            path.cubicTo(ctrl1, ctrl2, end_pos)
        
        self.setPath(path)

    def _should_use_straight_line(self):
        """判断是否使用直线（同侧引脚用曲线，异侧用直线）"""
        start_side = self.start_pin.pin_name
        end_side = self.end_pin.pin_name
        return (start_side in ["left", "right"] and end_side in ["left", "right"]) or \
               (start_side in ["plus", "minus"] and end_side in ["plus", "minus"])
