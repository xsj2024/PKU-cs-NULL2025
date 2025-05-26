from PyQt5.QtWidgets import QDoubleSpinBox, QGraphicsPathItem, QGraphicsRectItem, QMainWindow, QDockWidget, QFormLayout, QLineEdit, QWidget
from Components.ComponentItem import GraphicComponentItem
from Components.components import PinItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QPixmap, QPainterPath, QColor

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
        super().__init__(name, "OSC", "icons/oscilloscope.png")
        self.params = {
            "time_range": 0.02,  # 默认20ms
            "show_waveform": True,
            "ch1_scale": 1.0,
            "ch2_scale": 1.0
        }
        # 通道连接状态
        self.connected_nodes = {"CH1": None, "CH2": None}
        self.window = None  # 波形窗口引用

    def show_window(self):
        """显示/激活波形窗口"""
        if not self.window:
            self.window = OscilloscopeWindow()
        self.window.show()
        self.window.activateWindow()
    
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np

class OscilloscopeWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("示波器")
        self.setGeometry(100, 100, 800, 600)
        
        # Matplotlib图形设置
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.setCentralWidget(self.canvas)
        
        # 初始化曲线
        self.line1, = self.ax1.plot([], [], 'r-', label='CH1')
        self.line2, = self.ax2.plot([], [], 'b-', label='CH2')
        self.setup_axes()

        self.cursor_v1 = self.ax1.axvline(0, color='gray', linestyle='--')
        self.cursor_v2 = self.ax2.axvline(0, color='gray', linestyle='--')
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def on_mouse_move(self, event):
        if event.inaxes:
            x = event.xdata
            self.cursor_v1.set_xdata([x, x])
            self.cursor_v2.set_xdata([x, x])
            self.canvas.draw()

    def setup_axes(self):
        """配置坐标轴样式"""
        for ax in [self.ax1, self.ax2]:
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend(loc='upper right')
        self.ax1.set_ylabel("CH1 (V)")
        self.ax2.set_ylabel("CH2 (V)")
        self.ax2.set_xlabel("Time (s)")

    def update_waveforms(self, time, ch1_data, ch2_data):
        """更新波形数据"""
        print("Updating waveforms...")
        self.line1.set_data(time, ch1_data)
        self.line2.set_data(time, ch2_data)
        
        # 自动调整坐标范围
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.set_xlim(time[0], time[-1])
        
        self.canvas.draw()

    def show_fft(self, time, ch1_data):
        from scipy.fft import fft
        yf = fft(ch1_data)
        xf = np.linspace(0, 1/(time[1]-time[0]), len(time))
        self.ax1.clear()
        self.ax1.plot(xf, np.abs(yf))
        self.ax1.set_xlabel('Frequency (Hz)')
        self.canvas.draw()