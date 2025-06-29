from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene
from PyQt5.QtCore import QRectF, Qt, QLineF
from PyQt5.QtGui import QPainterPath, QPen, QColor, QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMainWindow, QAction, QToolBar
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import QPointF, pyqtSignal, QObject
import math

class PinProxy(QObject):
    """代理类，用于处理引脚的信号和槽"""
    position_changed = pyqtSignal()  # 位置变化信号

class PinItem(QGraphicsEllipseItem):
    def __init__(self, parent_component, pin_name, pos_x, pos_y):
        super().__init__(-6, -6, 12, 12, parent=parent_component)
        self.setPos(pos_x, pos_y)
        self.setBrush(QBrush(QColor(100, 100, 255)))
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.pin_name = pin_name
        self.parent_component = parent_component
        self.connected_wires = []
        self.node_name = None
        self.voltage = None
        self.ac_voltage = None
        self.setAcceptHoverEvents(True)
        self.voltage_label = None
        self.proxy = PinProxy()
        self.posChanged = self.proxy.position_changed
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        #为吸附功能添加一个专门的高亮状态
        self.snap_highlighted = False

    def itemChange(self, change, value):
        #ItemPositionChange的正确枚举值是1，但为了兼容性，保留原来的27或使用枚举
        if change == QGraphicsItem.ItemScenePositionHasChanged:
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

    # 【新增】专门用于吸附时的高亮，避免与悬停高亮冲突
    def set_snap_highlight(self, highlighted):
        self.snap_highlighted = highlighted
        if highlighted:
            self.setBrush(QBrush(QColor(100, 255, 100))) # 使用绿色作为吸附高亮色
            self.setZValue(3) # 最高层级
        else:
            # 恢复时，要变回原来的蓝色
            self.setBrush(QBrush(QColor(100, 100, 255)))
            self.setZValue(0)
        
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
        # 恢复外观，但要检查是否正处于吸附高亮状态
        if not self.snap_highlighted:
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
        self.temp_wire = None
        self.main_window = parent
        self.temp_start_pin = None # 【修正】将temp_start_pin的初始化移到此处

        # 【新增】引脚吸附相关的属性
        self.snap_distance = 15  # 像素单位，鼠标离引脚多近时触发吸附
        self.hovered_snap_pin = None # 当前准备吸附的目标引脚

    def start_wire_from_pin(self, pin):
        # 【优化】设置鼠标指针为十字形并使用虚线
        if self.main_window and self.main_window.view:
            self.main_window.view.setCursor(Qt.CrossCursor)
        self.temp_start_pin = pin
        self.temp_wire = QGraphicsLineItem(
            pin.scenePos().x(), pin.scenePos().y(),
            pin.scenePos().x(), pin.scenePos().y()
        )
        self.temp_wire.setPen(QPen(QColor(50, 150, 250), 2, Qt.DotLine))
        self.addItem(self.temp_wire)

    def mouseMoveEvent(self, event):
        #重写此方法以实现吸附逻辑
        if self.temp_wire:
            current_pos = event.scenePos()
            target_pin = None
            
            # 查找离鼠标最近的有效引脚
            min_dist = self.snap_distance
            # 遍历场景中的所有图形项来找到PinItem
            for item in self.items():
                if isinstance(item, PinItem):
                    if item == self.temp_start_pin:
                        continue # 跳过起始引脚
                    dist = math.hypot(item.scenePos().x() - current_pos.x(), item.scenePos().y() - current_pos.y())
                    if dist < min_dist:
                        min_dist = dist
                        target_pin = item

            # 处理高亮状态的切换
            if self.hovered_snap_pin and self.hovered_snap_pin != target_pin:
                self.hovered_snap_pin.set_snap_highlight(False) # 取消上一个目标的高亮
            
            self.hovered_snap_pin = target_pin
            
            # 更新临时导线的末端位置
            line = self.temp_wire.line()
            if self.hovered_snap_pin:
                self.hovered_snap_pin.set_snap_highlight(True) # 高亮当前目标
                line.setP2(self.hovered_snap_pin.scenePos()) # 吸附到目标引脚中心
            else:
                line.setP2(current_pos) # 未找到目标，跟随鼠标
            
            self.temp_wire.setLine(line)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        #使用吸附的引脚
        if self.temp_start_pin:
            # 恢复鼠标指针
            if self.main_window and self.main_window.view:
                self.main_window.view.setCursor(Qt.ArrowCursor)

            # 优先使用被吸附的引脚作为终点
            end_pin = self.hovered_snap_pin

            if end_pin:
                wire = WireItem(self.temp_start_pin, end_pin)
                #使用命令管理器添加连线
                if self.main_window and hasattr(self.main_window, 'command_manager'):
                    self.main_window.add_wire_with_command(wire)
                else:
                    #备用方案：直接添加
                    self.addItem(wire)
                    self.wires.append(wire)
            
            # 清理临时项和状态
            if self.hovered_snap_pin:
                self.hovered_snap_pin.set_snap_highlight(False)
                self.hovered_snap_pin = None

            if self.temp_wire:
                self.removeItem(self.temp_wire)
            self.temp_wire = None
            self.temp_start_pin = None
        
        super().mouseReleaseEvent(event)

    def pin_hover(self, pin, is_hovered):
        """处理引脚悬停事件"""
        if is_hovered:
            if pin.voltage is not None:
                self.main_window.voltage_label.setText(f"Voltage at {pin.pin_name}: {pin.voltage:.2f} V")
            else:
                self.main_window.voltage_label.setText(f"Voltage at {pin.pin_name}: N/A")
        else:
            # 【修正】恢复默认文本
            self.main_window.voltage_label.setText("悬停引脚查看电压")

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

class WireItem(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setZValue(1)
        
        # 连接信号以动态更新路径
        self.start_pin.proxy.position_changed.connect(self.update_path)
        self.end_pin.proxy.position_changed.connect(self.update_path)
        
        # 确保导线被添加到引脚的连接列表中
        start_pin.add_wire(self)
        end_pin.add_wire(self)

        self.update_path()

    def update_path(self):
        """生成平滑的导线路径（贝塞尔曲线或智能折线）"""
        start_pos = self.start_pin.scenePos()
        end_pos = self.end_pin.scenePos()
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # 根据引脚相对位置选择路径类型
        if self._should_use_straight_line():
            path.lineTo(end_pos)
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