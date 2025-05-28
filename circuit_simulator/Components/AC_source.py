from PyQt5.QtWidgets import QDoubleSpinBox, QGraphicsPathItem, QGraphicsRectItem, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QLineEdit, QDockWidget
from Components.ComponentItem import GraphicComponentItem
from Components.components import PinItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QPixmap, QPainterPath, QColor
from PyQt5.QtCore import pyqtSignal

class ACSourceItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "V_AC")
        self.params.update({
            "waveform": "SIN",  # SIN/SQUARE/PULSE等
            "amplitude": 5.0,  # 幅值 (V)
            "frequency": 50,   # 频率 (Hz)
            "phase": 0,         # 相位 (度)
            "dc_offset": 0,
            # 方波特有
            "duty_cycle": 50,    # 占空比%
            # 脉冲特有
            "rise_time": 1e-6,   # 上升时间
            "fall_time": 1e-6   # 下降时间
        })

    def _update_freq(self, value):
        self.params["frequency"] = value

    def spice_description(self):
        if self.params["waveform"] == "SIN":
            return (f"SIN({self.params['dc_offset']} "
                f"{self.params['amplitude']} {self.params['frequency']} "
                f"0 0 {self.params.get('phase', 0)})")
        # 方波实例：circuit.V('name', 'node+', 'node-', 'PULSE(初始值 峰值 延迟时间 上升时间 下降时间 脉宽 周期)')
        elif self.params["waveform"] == "SQUARE":
            return (f"PULSE("+
                str(self.params["dc_offset"])+" "
                f"{self.params['amplitude']} 0 "
                f"0 0 {1/self.params['frequency'] * self.params['duty_cycle'] / 100} "
                f"{1/self.params['frequency']})")
        elif self.params["waveform"] == "PULSE":
            return (f"PULSE(0 {self.params['amplitude']} 0 "
                f"{self.params['rise_time']} {self.params['fall_time']} "
                f"{1/self.params['frequency'] - self.params['rise_time'] - self.params['fall_time']} "
                f"{1/self.params['frequency']})")
    
    def set_param(self, param_name, value):
        """设置参数值"""
        if param_name in self.params:
            # 检查值的范围
            if param_name == "amplitude":
                if value < 0:
                    print("幅值不能为负数!")
                else:
                    self.params[param_name] = value
            elif param_name == "frequency":
                if value <= 0:
                    print("频率必须大于0!")
                else:
                    self.params[param_name] = value
            elif param_name == "phase":
                if not (0 <= value < 360):
                    print("相位必须在0到360度之间!")
                else:
                    self.params[param_name] = value
            elif param_name == "duty_cycle":
                if not (0 <= value <= 100):
                    print("占空比必须在0到100%之间!")
                else:
                    self.params[param_name] = value
            elif param_name in ["rise_time", "fall_time"]:
                if value < 0:
                    print(f"{param_name}不能为负数!")
                else:
                    self.params[param_name] = value
            elif param_name == "dc_offset":
                if not (-1000 <= value <= 1000):
                    print("直流偏置必须在-1000到1000V之间!")
                else:
                    self.params[param_name] = value
            elif param_name == "waveform":
                if value not in ["SIN", "SQUARE", "PULSE"]:
                    print("波形类型必须是SIN, SQUARE或PULSE!")
                else:
                    self.params[param_name] = value
        else:
            raise ValueError(f"Parameter {param_name} not found in {self.name}")

class OscilloscopeItem(GraphicComponentItem):
    def __init__(self, name):
        super().__init__(name, "OSC")
        self.params = {
            "time_range": 0.02,  # 默认20ms
            "show_waveform": True,
            "ch1_scale": 1.0,
            "ch2_scale": 1.0,
            "mode": "Both", #"CH1","CH2","Both","XY"
            "auto_scale": True,  # 是否自动缩放
        }
        # 连接状态
        self.connected_nodes = {"CH1": None, "CH2": None}
        self.window = None  # 波形窗口引用

    def show_window(self):
        """显示/激活波形窗口"""
        if not self.window:
            self.window = OscilloscopeWindow(self)
        self.window.show()
        self.window.activateWindow()
        
    def set_param(self, param_name, value, force_update=False):
        """设置参数值"""
        rerun = False  # 是否需要重新运行仿真
        if param_name in self.params:
            if param_name == "mode" and value not in ["Both", "CH1", "CH2", "XY"]:
                print("显示模式必须是 Both/CH1/CH2/XY!")
                return
            
            if param_name == "time_range":
                if value <= 0:
                    print("时间范围必须大于0!")
                    return
                elif value != self.params["time_range"]:
                    rerun = True
            self.params[param_name] = value
            if rerun:
                print(f"Parameter {param_name} changed, you can rerun simulation.")
                # 这里可以添加重新运行仿真的逻辑

            if self.window and force_update:
                self.window.on_params_changed()
        else:
            raise ValueError(f"Parameter {param_name} not found in {self.name}")
        
    
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np

class OscilloscopeWindow(QMainWindow):
    def __init__(self, osc_item, parent=None):
        super().__init__(parent)
        self.osc_item = osc_item
        self.setWindowTitle(f"示波器 - {osc_item.name}")
        self.setGeometry(100, 100, 800, 600)
        
        # 主控件
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        
        # 控制面板
        self._create_control_panel()
        
        # Matplotlib图形设置
        self.figure = plt.Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.layout.addWidget(self.canvas)
        
        # 初始化图形
        self.setup_axes()
        
        # 初始化数据
        self.time_data = np.array([])
        self.ch1_data = np.array([])
        self.ch2_data = np.array([])

    def _create_control_panel(self):
        """创建控制面板"""
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 时间范围控制
        self.time_range_spin = QDoubleSpinBox()
        self.time_range_spin.setRange(0.001, 10.0)
        self.time_range_spin.setValue(self.osc_item.params["time_range"])
        self.time_range_spin.setSuffix(" s")
        self.time_range_spin.valueChanged.connect(self.update_time_range)
        
        # 显示模式选择
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Both", "CH1", "CH2", "XY"])
        self.display_mode_combo.setCurrentText(self.osc_item.params["mode"])
        self.display_mode_combo.currentTextChanged.connect(self.update_display_mode)
        
        # 自动缩放复选框
        self.auto_scale_check = QCheckBox("自动缩放")
        self.auto_scale_check.setChecked(self.osc_item.params["auto_scale"])
        self.auto_scale_check.stateChanged.connect(self.update_auto_scale)
        
        # 添加到布局
        control_layout.addWidget(QLabel("时间范围:"))
        control_layout.addWidget(self.time_range_spin)
        control_layout.addWidget(QLabel("显示模式:"))
        control_layout.addWidget(self.display_mode_combo)
        control_layout.addWidget(self.auto_scale_check)
        control_layout.addStretch()
        
        self.layout.addWidget(control_panel)

    def setup_axes(self):
        """配置坐标轴"""
        self.figure.clear()
        
        mode = self.osc_item.params["mode"]
        
        if mode == "Both":
            self.ax1 = self.figure.add_subplot(211)
            self.ax2 = self.figure.add_subplot(212, sharex=self.ax1)
            
            # 初始化曲线
            self.line1, = self.ax1.plot([], [], 'r-', label='CH1')
            self.line2, = self.ax2.plot([], [], 'b-', label='CH2')
            
            # 配置坐标轴
            for ax in [self.ax1, self.ax2]:
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.legend(loc='upper right')
            
            self.ax1.set_ylabel("CH1 (V)")
            self.ax2.set_ylabel("CH2 (V)")
            self.ax2.set_xlabel("Time (s)")
            
        elif mode == "CH1":
            self.ax1 = self.figure.add_subplot(111)
            self.line1, = self.ax1.plot([], [], 'r-', label='CH1')
            self.ax1.grid(True, linestyle='--', alpha=0.6)
            self.ax1.legend(loc='upper right')
            self.ax1.set_ylabel("CH1 (V)")
            self.ax1.set_xlabel("Time (s)")
            
        elif mode == "CH2":
            self.ax2 = self.figure.add_subplot(111)
            self.line2, = self.ax2.plot([], [], 'b-', label='CH2')
            self.ax2.grid(True, linestyle='--', alpha=0.6)
            self.ax2.legend(loc='upper right')
            self.ax2.set_ylabel("CH2 (V)")
            self.ax2.set_xlabel("Time (s)")
            
        elif mode == "XY":
            self.ax_xy = self.figure.add_subplot(111)
            self.line_xy, = self.ax_xy.plot([], [], 'g-', label='X-Y')
            self.ax_xy.grid(True, linestyle='--', alpha=0.6)
            self.ax_xy.legend(loc='upper right')
            self.ax_xy.set_xlabel("CH1 (V)")
            self.ax_xy.set_ylabel("CH2 (V)")
        
        self.figure.tight_layout()
        self.canvas.draw()

    def update_waveforms(self, time, ch1_data, ch2_data):
        """更新波形数据"""
        self.time_data = time
        self.ch1_data = ch1_data
        self.ch2_data = ch2_data
        
        mode = self.osc_item.params["mode"]
        auto_scale = self.osc_item.params["auto_scale"]
        
        if mode == "Both":
            self.line1.set_data(time, ch1_data)
            self.line2.set_data(time, ch2_data)
            
            if auto_scale:
                self.ax1.relim()
                self.ax1.autoscale_view()
                self.ax2.relim()
                self.ax2.autoscale_view()
            
            self.ax2.set_xlim(time[0], time[-1])
            
        elif mode == "CH1":
            self.line1.set_data(time, ch1_data)
            if auto_scale:
                self.ax1.relim()
                self.ax1.autoscale_view()
            self.ax1.set_xlim(time[0], time[-1])
            
        elif mode == "CH2":
            self.line2.set_data(time, ch2_data)
            if auto_scale:
                self.ax2.relim()
                self.ax2.autoscale_view()
            self.ax2.set_xlim(time[0], time[-1])
            
        elif mode == "XY":
            self.line_xy.set_data(ch1_data, ch2_data)
            if auto_scale:
                self.ax_xy.relim()
                self.ax_xy.autoscale_view()
        
        self.canvas.draw()

    def update_display_mode(self):
        """更新显示模式"""
        self.osc_item.set_param("mode", self.display_mode_combo.currentText())
        self.setup_axes()
        if len(self.time_data) > 0:
            self.update_waveforms(self.time_data, self.ch1_data, self.ch2_data)

    def update_time_range(self, value):
        """更新时间范围"""
        self.osc_item.set_param("time_range", value)
        if len(self.time_data) > 0:
            self.update_waveforms(self.time_data, self.ch1_data, self.ch2_data)

    def update_auto_scale(self, state):
        """更新自动缩放状态"""
        self.osc_item.params["auto_scale"] = (state == Qt.Checked)
        if len(self.time_data) > 0:
            self.update_waveforms(self.time_data, self.ch1_data, self.ch2_data)
        
        # 更新显示
        self.update_display_mode()

    def on_params_changed(self):
        """当参数改变时调用"""
        self.update_display_mode()
        self.update_time_range(self.osc_item.params["time_range"])
        self.auto_scale_check.setChecked(self.osc_item.params["auto_scale"])
        self.display_mode_combo.setCurrentText(self.osc_item.params["mode"])
        
        # 重新绘制图形
        if len(self.time_data) > 0:
            self.update_waveforms(self.time_data, self.ch1_data, self.ch2_data)