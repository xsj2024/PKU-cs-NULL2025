from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QGraphicsItem
from Components.components import PinItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject

class ComponentProxy(QObject):
    """代理类，用于处理引脚的信号和槽"""
    position_changed = pyqtSignal()  # 位置变化信号

class GraphicComponentItem(QGraphicsPixmapItem):
    def __init__(self, name, spice_type, icon_path=None):
        super().__init__()
        self.root = "./circuit_simulator/"
        self.name = name
        self.spice_type = spice_type
        self.pins = {}
        
        # 特定的模型参数在每个元件的子类中定义
        self.params = {
            "name": name,
            "spice_type": spice_type
        }
        
        # 加载图标
        self._load_icon(icon_path or self._default_icon_path())
        self._setup_pins()
        
        # 启用交互
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.proxy = ComponentProxy()  # 创建代理类实例
        self.positionChanged = self.proxy.position_changed  # 位置变化信号

        self.posChanged = self.proxy.position_changed  # 位置变化信号

    def _default_icon_path(self):
        """根据类型返回默认图标路径"""
        return self.root +{
            "R": "icons/R.png",
            "C": "icons/C.png",
            "V": "icons/V.png",
            "D": "icons/D.png",
            "GND": "icons/GND.png",
            "L": "icons/L.png",
            "V_AC": "icons/AC.png",
            "OSC": "icons/osc.png",
        }.get(self.spice_type, "icons/default.png")

    def _load_icon(self, path):
        """加载并缩放图标"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"Warning: Icon not found at {path}. Using default gray icon.")
            pixmap = QPixmap(100, 60)
            pixmap.fill(Qt.gray)
        self.setPixmap(pixmap.scaled(75, 50, Qt.KeepAspectRatio))

    def _setup_pins(self):
        """根据元件类型设置引脚位置"""
        for pin in self.pins.values():
            if pin.scene():
                pin.scene().removeItem(pin)
        self.pins.clear()  # 清空之前的引脚
        rect = self.boundingRect()
        if self.spice_type == "R":
            self.pins["left"] = PinItem(self, "left", rect.left(), rect.center().y())
            self.pins["right"] = PinItem(self, "right", rect.right(), rect.center().y())
        elif self.spice_type == "V":
            self.pins["plus"] = PinItem(self, "plus", rect.right(), rect.center().y())
            self.pins["minus"] = PinItem(self, "minus", rect.left(), rect.center().y())
        elif self.spice_type == "GND":
            self.pins["gnd"] = PinItem(self, "gnd", rect.center().x(), rect.top())
        elif self.spice_type == "D":
            self.pins["anode"] = PinItem(self, "anode", rect.left(), rect.center().y())
            self.pins["cathode"] = PinItem(self, "cathode", rect.right(), rect.center().y())
        elif self.spice_type == "C":
            self.pins["left"] = PinItem(self, "left", rect.left(), rect.center().y())
            self.pins["right"] = PinItem(self, "right", rect.right(), rect.center().y())
        elif self.spice_type == "L":
            self.pins["left"] = PinItem(self, "left", rect.left(), rect.center().y())
            self.pins["right"] = PinItem(self, "right", rect.right(), rect.center().y())
        elif self.spice_type == "V_AC":
            self.pins["plus"] = PinItem(self, "ac", rect.left(), rect.center().y())
            self.pins["minus"] = PinItem(self, "norm", rect.right(), rect.center().y())
        elif self.spice_type == "OSC":
            #引脚在左下方和右下方，3/4处
            self.pins["ch1"] = PinItem(self, "ch1", rect.left() * 1 / 2, rect.bottom() * 3 / 4)
            self.pins["ch2"] = PinItem(self, "ch2", rect.right() * 1 / 2, rect.bottom() * 3 / 4)

    def paint(self, painter, option, widget=None):
        """自定义绘制（图标+引脚）"""
        super().paint(painter, option, widget)
        
        # 选中时高亮
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())

    def get_editable_parameters(self):
        """返回需要编辑的参数列表"""
        pass
    
    def set_update_parameters(self, params):
        """更新参数"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: {key} is not a valid parameter for {self.spice_type}.")