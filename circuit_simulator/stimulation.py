from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction
from spice_generator import generate_spice_netlist
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QListWidget, 
    QToolBar, QTabWidget, QWidget, QVBoxLayout, QPushButton
)
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QToolBar, QAction, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QBrush, QTransform,QKeySequence, QPainterPath
from PyQt5.QtWidgets import QShortcut, QLabel
from shortcuts_manager import shortcutManager,shortcutSettingDialog
from files_manager import FilesManager
from command_manager import (
    CommandManager, AddComponentCommand, RemoveComponentCommand, 
    MoveComponentCommand, AddWireCommand, RemoveWireCommand, ClearSceneCommand
)
from PyQt5.QtGui import QKeySequence
from Components.AC_source import ACSourceItem, OscilloscopeItem
from parameter_editor import ParameterEditorDock
from Components.components import PinItem, WireItem, CircuitScene
from Components.ComponentItem import GraphicComponentItem
from Components.basic import ResistorItem, CapacitorItem, InductorItem, VoltageSourceItem, GroundItem, DiodeItem
import numpy as np
from PyQt5.QtGui import QPixmap, QPalette, QBrush #用于设置背景
from background import BackgroundDialog
from PyQt5.QtCore import QFileInfo #将字符串路径和文件系统的文件关联起来用
import json #用于JSON文件操作
from PyQt5.QtCore import QStandardPaths, QDir #用于确保目录存在
#新增：
from terminal import TerminalWidget,SignallingStdout
from PyQt5.QtWidgets import QSplitter
from ai_manager import AiConfigDialog

class CircuitSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt + PySpice 电路模拟器")
        self.setGeometry(500, 500, 1400, 800)
        
        # 创建左侧元件停靠窗口
        self.component_dock = self._create_component_dock()
        # 参数编辑器初始化
        self.param_editor = ParameterEditorDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.param_editor)
        self.param_editor.setStyleSheet("""
    QDockWidget {
        background: rgba(45, 45, 45, 0.4);  /* 70%不透明深灰 */
        border: 2px solid rgba(80, 80, 80, 0.9);
        border-radius: 8px;
    }
    QDockWidget::title {
        text-align: left;
        background: rgba(60, 60, 60, 0.7);
        padding: 6px;
        color: white;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    QDockWidget > QWidget {  /* 内容区域 */
        background: rgba(50, 50, 50, 0.6);
        border-radius: 8px;
    }

        """)

        # 初始化场景和视图
        self.scene = CircuitScene(self)
        self.scene.setBackgroundBrush(QBrush(Qt.transparent)) #设置场景为透明
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)  # 启用抗锯齿
        self.view.setRenderHint(QPainter.TextAntialiasing)  # 文本抗锯齿
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        # 设置QGraphicsView透明和视口背景透明
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.viewport().setStyleSheet("background: transparent;")
        
        # 创建终端控件
        self.terminal = TerminalWidget(self)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(45, 45, 45, 0.4);  /* 70%不透明深灰 */
                color: #A9B7C6; /* 浅灰色文本 */
                font-family: "Consolas", "Courier New", monospace;
                font-size: 10pt;
                border: 1px solid #3C3C3C;
            }
        """)
        self.terminal.setMinimumHeight(100)
        
        # 主布局
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;") #主窗口设置透明
        
        self.splitter = QSplitter(Qt.Vertical, central_widget) # 创建一个垂直方向的 QSplitter
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.terminal)
        initial_view_height = int(self.height() * 0.75) if self.height() > 400 else 600
        initial_terminal_height = int(self.height() * 0.25) if self.height() > 400 else 200
        self.splitter.setSizes([initial_view_height, initial_terminal_height])

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) #无外边距
        layout.setSpacing(0) #试图和终端无边距
        layout.addWidget(self.splitter)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # 创建工具栏
        self._create_menubar()
        
        # 状态栏显示操作提示
        self.statusBar().showMessage("拖放元件并连线，点击仿真运行SPICE")
        #为状态栏提供一个对比背景和浅色文字
        self.statusBar().setStyleSheet("""
    QStatusBar {
        background: rgba(45, 45, 45, 0.4);  /* 70%不透明深灰 */
        color: #FFFFFF;      /* 白色文字 */
        border-top: 1px solid #505050;
        font-family: "Segoe UI";
        font-size: 20px;
    }
    QStatusBar::item {
        border: none;
        padding: 0 5px;
    }
    QLabel {
        color: #FFFFFF;
        font-family: "Segoe UI";
        font-size: 20px;
    }

        """)

        # 重定向
        self.stdout_redirector = SignallingStdout(self)
        self.stdout_redirector.text_written.connect(self.terminal.append_text)
        sys.stdout = self.stdout_redirector
        self.stderr_redirector = SignallingStdout(self)
        self.stderr_redirector.text_written.connect(self.terminal.append_text) # 可以连接到同一个槽
        sys.stderr = self.stderr_redirector

        # 显示初始提示符
        self.terminal.show_prompt()

        # 快捷键初始化
        self.shortcut_manager = shortcutManager(self)
        self._setup_shortcuts()

        #背景图默认数据
        base_dir = os.path.dirname(os.path.abspath(__file__)) # 当前文件所在目录的绝对路径
        self.default_background_images = [
            os.path.join(base_dir, "default_bkgrounds", "nakano_miku_1.jpg"),
            os.path.join(base_dir, "default_bkgrounds", "nakano_miku_2.jpg"),
            os.path.join(base_dir, "default_bkgrounds", "nakano_miku_3.jpg"),
            os.path.join(base_dir, "default_bkgrounds", "test.jpg"),
            os.path.join(base_dir, "default_bkgrounds", "test2.png"),
            os.path.join(base_dir, "default_bkgrounds", "pure_white.jpg"),
            #可以添加更多图片
        ]
        self.background_config_path = os.path.join(base_dir,"user_background.json") #统一在该文件进行读取图片路径
        self._current_background_path = None # 当前背景的路径
        #背景图初始化
        self._set_initial_default_background()
        # 确保在调整窗口大小时背景图片能够正确更新
        self.resizeEvent_orig = self.resizeEvent
        self.resizeEvent = self._custom_resize_event

        #ai_Info地址
        self.ai_config_file_path = os.path.join(base_dir, "ai_Info.json")

        # 文件管理初始化
        self.current_file_path = None
        self.saved = True
        self.files_manager = FilesManager(self)

        # 命令管理初始化
        self.command_manager = CommandManager()
        self.command_manager.set_main_window(self)

        # 连接场景选择变化信号
        self.scene.selectionChanged.connect(self._on_selection_changed)

        # 在状态栏中增加一个悬停引脚电压的显示
        self.voltage_label = QLabel("悬停引脚查看电压")
        # 处在于状态栏的右侧
        self.voltage_label.setAlignment(Qt.AlignRight)
        self.statusBar().addPermanentWidget(self.voltage_label)
        self.voltage_label.setStyleSheet("""
    QLabel {
        color: #FFFFFF;
        font-family: "Segoe UI";
        font-size: 20px;
        padding-right: 10px;
    }
""")


    def get_component_classes_map(self):
        '''
        该函数为FilesManager提供所有元件种类
        若后续还有新的元件需要在下表中添加
        '''
        return {
            "R": ResistorItem,
            "V": VoltageSourceItem,
            "GND": GroundItem,
            "D": DiodeItem,
            "C": CapacitorItem,
            "L": InductorItem,
            "V_AC": ACSourceItem,
            "OSC": OscilloscopeItem,
            "WireItem": WireItem,
            "GraphicComponentItem": GraphicComponentItem
        }

    def _set_saved(self, saved):
        self.saved = saved
        self._update_window_title()

    # 更新窗口名称
    def _update_window_title(self): 
        title = "PyQt + PySpice 电路模拟器"
        if self.current_file_path:
            fileName = os.path.basename(self.current_file_path)
            title = f"{fileName} - {title}"
        else:
            title = f"未命名 - {title}"
        
        if not self.saved:
            title = "*" + title
        self.setWindowTitle(title)

    def new_file(self):
        self.files_manager.new_file()
        self.command_manager.clear_history()

    def save_file(self):
        self.files_manager.save_file()
        self.command_manager.clear_history()

    def open_file(self):
        self.files_manager.open_file()
        self.command_manager.clear_history()

    def save_file_as(self):
        self.command_manager.clear_history()
        return self.files_manager.save_file_as()

    def _on_selection_changed(self):
        items = self.scene.selectedItems()
        if len(items) == 1 and isinstance(items[0], GraphicComponentItem):
            self.param_editor.edit_component(items[0])
        else:
            self.param_editor.clear()

    def _create_component_dock(self):
        """创建左侧元件列表停靠栏"""
        dock = QDockWidget("元件库", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        # 设置停靠窗口的大小
        dock.setMinimumWidth(350)
        
        # 设置QDockWidget本身背景透明
        dock.setStyleSheet("QDockWidget { background: transparent; border: 1px solid gray; }")

        # 希望不能被拖动或者改变大小或者关闭
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setFloating(False)  # 禁止浮动

        # 使用选项卡分类元件
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
    QDockWidget {
        background: rgba(45, 45, 45, 0.4);
        border: 2px solid rgba(80, 80, 80, 0.9);
        border-radius: 8px;
    }
    QDockWidget::title {
        text-align: left;
        background: rgba(60, 60, 60, 0.7);
        padding: 6px;
        color: white;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    QTabWidget::pane {
        border: none;
        background: rgba(50, 50, 50, 0.6);
        border-radius: 8px;
    }
    QTabBar::tab {
        background: rgba(80, 80, 80, 0.6);
        color: white;
        padding: 8px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background: rgba(120, 120, 120, 0.7);
    }
    QPushButton {
        background: rgba(70, 70, 70, 0.7);
        color: white;
        border: 1px solid rgba(100, 100, 100, 0.8);
        border-radius: 4px;
        padding: 8px;
    }
    QPushButton:hover {
        background: rgba(90, 90, 90, 0.8);
    }
""")
        # 基础元件选项卡
        basic_tab = QWidget()
        basic_tab.setStyleSheet("background: transparent;")
        basic_layout = QVBoxLayout()
        self._add_component_buttons(basic_layout, ["电阻", "电压源", "接地"])
        basic_tab.setLayout(basic_layout)
        
        # 半导体选项卡（未来扩展）
        semi_tab = QWidget()
        semi_tab.setStyleSheet("background: transparent;")
        semi_layout = QVBoxLayout()
        self._add_component_buttons(semi_layout, ["二极管"])
        semi_tab.setLayout(semi_layout)
        
        # 交流元件选项卡
        ac_tab = QWidget()
        ac_tab.setStyleSheet("background: transparent;")
        ac_layout = QVBoxLayout()
        self._add_component_buttons(ac_layout, ["交流源", "电容", "电感" , "示波器"])
        ac_tab.setLayout(ac_layout)

        tab_widget.addTab(basic_tab, "基础元件")
        tab_widget.addTab(semi_tab, "半导体")
        tab_widget.addTab(ac_tab, "交流元件")

        dock.setWidget(tab_widget)
        dock.setStyleSheet("""
            QDockWidget {
                background: transparent;
                border: 2px solid rgb(100, 100, 100, 0.9);
            }
            QDockWidget::title {
                text-align: left;
                background: rgba(50, 50, 50, 0.55);
                padding: 6px;
                color: white;
                border: none;
            }
        """)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    
    def _add_component_buttons(self, layout, components, enabled=True):
        """动态添加元件按钮到布局"""
        for comp in components:
            btn = QPushButton(comp)
            btn.setEnabled(enabled)
            btn.clicked.connect(lambda _, c=comp: self._add_component(c))
            # 修改按钮样式适应透明背景
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px;
                    font-size: 14px;
                    text-align: left;
                    border: 1px solid rgba(204, 204, 204, 0.6); /* 半透明浅色边框 */
                    border-radius: 4px;
                    background-color: rgba(70, 70, 70, 0.5);  /* 半透明深色背景 */
                    color: white;                             /* 白色文字 */
                }
                QPushButton:hover {
                    background-color: rgba(90, 90, 90, 0.5); /* 悬停时略亮/更不透明 */
                    border-color: rgba(221, 221, 221, 0.7);
                }
                QPushButton:pressed {
                    background-color: rgba(50, 50, 50, 0.5);  /* 按下时 */
                }
                QPushButton:disabled { /* 为禁用状态也提供样式 */
                    background-color: rgba(100, 100, 100, 0.2);
                    color: rgba(200, 200, 200, 0.5);
                    border-color: rgba(150, 150, 150, 0.3);
                }
            """)
            layout.addWidget(btn)
        layout.addStretch()  # 添加弹性空间

    def _create_menubar(self):
        """创建菜单栏按钮"""
        main_menu_bar = self.menuBar()

        # 为菜单栏提供半透明深色背景，设置按钮文字为浅色文字
        main_menu_bar.setStyleSheet("""
            QToolBar {
                background: rgba(45, 45, 45, 0.65); /* 工具栏半透明深色背景 */
                border: 1px solid rgba(80, 80, 80, 0.5);
                padding: 2px;
                spacing: 4px; /* 项目间距 */
            }
            QToolButton { /* 针对工具栏中的按钮 (QAction) */
                color: white; /* 动作文字白色 */
                background-color: transparent; /* 按钮在工具栏上的背景透明 */
                padding: 5px;
                margin: 1px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: rgba(100, 100, 100, 0.55);
            }
            QToolButton:pressed {
                background-color: rgba(70, 70, 70, 0.65);
            }
            /* 如果工具栏有自己的标题 (例如可浮动时)，设置其颜色 */
            QToolBar QLabel { 
                color: white;
            }
        """)
        
        # 文件菜单
        file_menu = main_menu_bar.addMenu("文件(&F)") # alt + f 打开文件菜单
        # 新建文件
        action_new_file = QAction("新建文件", self)
        action_new_file.setStatusTip("创建一个新的电路文件")
        action_new_file.triggered.connect(self.new_file) # 连接到已有的 new_file 方法
        file_menu.addAction(action_new_file)
        # 打开文件
        action_open_file = QAction("打开文件", self)
        action_open_file.setStatusTip("打开一个已存在的电路文件")
        action_open_file.triggered.connect(self.open_file) # 连接到已有的 open_file 方法
        file_menu.addAction(action_open_file)
        # 保存文件
        action_save_file = QAction("保存文件", self)
        action_save_file.setStatusTip("保存当前电路文件")
        action_save_file.triggered.connect(self.save_file) # 连接到已有的 save_file 方法
        file_menu.addAction(action_save_file)
        # 另存文件
        action_save_as_file = QAction("另存文件", self)
        action_save_as_file.setStatusTip("将当前电路文件另存为新文件")
        action_save_as_file.triggered.connect(self.save_file_as) # 连接到已有的 save_file_as 方法
        file_menu.addAction(action_save_as_file)

        # 设置菜单
        settings_menu = main_menu_bar.addMenu("设置(&E)") # alt + e 打开设置
        # 背景设置
        action_set_background = QAction("背景设置", self) 
        action_set_background.setStatusTip("更改应用程序的背景图片")
        action_set_background.triggered.connect(self.open_background_dialog) # 连接到已有的方法
        settings_menu.addAction(action_set_background)
        #快捷键设置
        action_set_shortcuts = QAction("快捷键设置", self) 
        action_set_shortcuts.setStatusTip("自定义快捷键")
        action_set_shortcuts.triggered.connect(self.show_shortcut_settings) # 连接到已有的方法
        settings_menu.addAction(action_set_shortcuts)
        #ai设置
        action_edit_ai_config = QAction("AI配置", self)
        action_edit_ai_config.setStatusTip("打开并编辑AI配置文件")
        action_edit_ai_config.triggered.connect(self._open_ai_config_dialog)
        settings_menu.addAction(action_edit_ai_config)
        # 运行菜单
        run_menu = main_menu_bar.addMenu("运行(&R)")
        # 运行spice仿真
        action_simulate = QAction("运行SPICE仿真", self)
        action_simulate.setStatusTip("对当前电路进行SPICE仿真")
        action_simulate.triggered.connect(self._run_spice_simulation) # 连接到已有的方法
        run_menu.addAction(action_simulate)
        # 清除按钮
        action_clear_scene = QAction("清除场景", self)
        action_clear_scene.setStatusTip("清空当前画布上的所有元件和连线")
        action_clear_scene.triggered.connect(self._clear_scene) # 连接到已有的方法
        run_menu.addAction(action_clear_scene)

    def _open_ai_config_dialog(self):
        """打开一个对话框来编辑AI配置。"""
        dialog = AiConfigDialog(self.ai_config_file_path, self)
        dialog.exec_() # exec_() 使其成为模态对话框

    def show_shortcut_settings(self):
        self.shortcut_manager.show_settings_dialog()

    def _add_component(self, component_type):
        """向场景中添加元件"""
        if component_type == "R" or component_type == "电阻":
            item = ResistorItem(f"R{len(self.scene.components) + 1}")
        elif component_type == "V" or component_type == "电压源":
            item = VoltageSourceItem(f"V{len(self.scene.components) + 1}")
        elif component_type == "GND" or component_type == "接地":
            item = GroundItem(f"GND{len(self.scene.components) + 1}")
        elif component_type == "二极管" or component_type == "D":
            item = DiodeItem(f"D{len(self.scene.components) + 1}")
        elif component_type == "电容" or component_type == "C":
            item = CapacitorItem(f"C{len(self.scene.components) + 1}")
        elif component_type == "交流源" or component_type == "V_AC":
            item = ACSourceItem(f"AC{len(self.scene.components) + 1}")
        elif component_type == "电感" or component_type == "L":
            item = InductorItem(f"L{len(self.scene.components) + 1}")
        elif component_type == "OSC" or component_type == "示波器":
            item = OscilloscopeItem(f"OSC{len(self.scene.components) + 1}")

        # 使用命令管理器添加元件
        command = AddComponentCommand(self.scene, item)
        self.command_manager.execute_command(command)
        self.statusBar().showMessage(f"已添加 {item.name}")
        self._set_saved(False)

    def _run_spice_simulation(self):
        """生成SPICE网表并调用PySpice"""
        try:
            # 直接调用generate_spice_netlist函数
            circuit, has_ac_source = generate_spice_netlist(self.scene)

            # 打印网表（可调用PySpice仿真）
            print("生成的SPICE网表:")
            print(circuit)
            if has_ac_source:
                print("包含交流源，仿真将使用AC分析。")

                osc_time_ranges = [
                    osc.params["time_range"] 
                    for osc in self.scene.items() 
                    if isinstance(osc, OscilloscopeItem)
                ]
                osc = next((i for i in self.scene.items() if isinstance(i, OscilloscopeItem)), None)

                # 取最大时间范围（或平均/首个示波器的设置）
                time_range = max(osc_time_ranges) if osc_time_ranges else 0.02
                simulator = circuit.simulator()
                # 模拟操作(交流分析）
                analysis = simulator.transient(
                    step_time=time_range / 1000,  # 自动计算步长
                    end_time=time_range
                )
                print("仿真成功！")
                # 更新示波器波形
                if osc:
                    time = np.array(analysis.time)
                    ch1 = np.array(analysis[osc.connected_nodes["CH1"]]) if osc.connected_nodes["CH1"] in analysis.nodes else np.zeros_like(time)
                    ch2 = np.array(analysis[osc.connected_nodes["CH2"]]) if osc.connected_nodes["CH2"] in analysis.nodes else np.zeros_like(time)
        
                    osc.show_window()
                    osc.window.update_waveforms(time, ch1, ch2)
                # 更新所有引脚的电压信号函数
                dict = analysis.nodes
                for comp in self.scene.components:
                    for pin_name, pin_item in comp.pins.items():
                        # 先将引脚电压设为None
                        pin_item.set_ac_voltage(None)
                        # 获取引脚对应的SPICE节点名
                        node_name = pin_item.node_name
                        if node_name in dict:
                            # 设置引脚电压
                            pin_item.set_ac_voltage(dict[node_name])
                        elif node_name == '0':
                            # 如果是接地引脚，设置电压为0
                            pin_item.set_ac_voltage(0.0)
            else:
                print("不包含交流源，仿真将使用直流工作点分析。")
                
                # 模拟操作(直流工作点分析）
                simulator = circuit.simulator()
                analysis = simulator.operating_point()
                print("仿真成功！")
                for node in analysis.nodes.values():
                    print(f"Node {str(node)}: {float(node):.3f} V")
                
                # 更新所有引脚的电压值
                dict = analysis.nodes
                for comp in self.scene.components:
                    for pin_name, pin_item in comp.pins.items():
                        # 先将引脚电压设为None
                        pin_item.set_voltage(None)
                        # 获取引脚对应的SPICE节点名
                        node_name = pin_item.node_name
                        if node_name in dict:
                            # 设置引脚电压
                            pin_item.set_voltage(dict[node_name])
                        elif node_name == '0':
                            # 如果是接地引脚，设置电压为0
                            pin_item.set_voltage(0.0)

                    
        
        except ImportError:
            QMessageBox.critical(self, "错误", "未安装PySpice！请运行: conda install -c conda-forge PySpice==1.5")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"仿真失败: {str(e)}")
            print("仿真失败:", str(e))
            # 显示原始SPICE输出以调试
            if hasattr(simulator, 'stdout'):
                print("SPICE输出:", simulator.stdout)

    def _clear_scene(self):
        """清空场景"""
        command = ClearSceneCommand(self.scene)
        self.command_manager.execute_command(command)
        self.statusBar().showMessage("场景已清除")
        self._set_saved(False)

    def _setup_shortcuts(self):
        shortcut_callbacks = {
            "new_file": self.new_file,
            "save_file": self.save_file,
            "resave_file":self.save_file_as,
            "open_file": self.open_file,
            "add_resistor": lambda: self._add_component("R"),
            "add_voltage": lambda: self._add_component("V"),
            "add_gnd": lambda: self._add_component("GND"),
            "run_spice_simulation": self._run_spice_simulation,
            "clear_scene": self._clear_scene,
            "show_shortcut_settings":self.show_shortcut_settings,
            "change_background":self.open_background_dialog,
            "undo": self.undo_command,  # 新增
            "redo": self.redo_command,  # 新增
            "delete_selected": self.delete_selected  # 新增
        }
        self.shortcut_manager.register_all_shortcuts(shortcut_callbacks)

    def _update_oscilloscopes(self, analysis):
        for item in self.scene.items():
            if isinstance(item, OscilloscopeItem) and item.params["show_waveform"]:
                for channel in ["CH1", "CH2"]:
                    if item.connected_nodes[channel]:
                        self._draw_waveform(item, channel, analysis)

    def _draw_waveform(self, osc, channel, analysis):
        """绘制单个通道波形"""
        node = osc.connected_nodes[channel]
        if node not in analysis:
            return
        
        time = analysis.time
        voltage = analysis[node]
    
        # 归一化到示波器坐标系
        path = QPainterPath()
        x_scale = osc.plot_area.rect().width() / osc.params["time_range"]
        y_scale = osc.plot_area.rect().height() / (osc.params[f"{channel.lower()}_scale"] * 8)  # 8div
    
        path.moveTo(30, -voltage[0] * y_scale)
        for t, v in zip(time[1:], voltage[1:]):
            path.lineTo(30 + t * x_scale, -v * y_scale)
    
        osc.waveforms[channel].setPath(path)

    def _set_background_from_path(self, image_path):
        if not image_path or not QFileInfo(image_path).exists():
            print(f"警告: 背景图片路径无效或不存在: {image_path}")
            return False

        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print(f"错误: 无法加载图片 {image_path}")
                return False

            current_palette = self.palette()  #返回调色板对象（管理控件的各种颜色和画刷
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            current_palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            self.setPalette(current_palette)
            self.setAutoFillBackground(True)
            self._current_background_path = image_path
            self._save_background_setting()
            print(f"背景已设置为: {image_path}")
            return True
        except Exception as e:
            print(f"设置背景时出错 ({image_path}): {e}")
            return False

    def _set_initial_default_background(self):
        if self._set_background_from_path(self._load_background_setting_path()):
            return True
        if self.default_background_images:
            # 尝试设置列表中的第一个默认图片
            if not self._set_background_from_path(self.default_background_images[0]):
                print("未能成功设置初始默认背景。请检查图片路径和文件。")
                return False
            return True
        else:
            print("没有默认背景图片，未初始背景")
            return False

    def open_background_dialog(self):
        dialog = BackgroundDialog(self,self.default_background_images)
        dialog.exec_()
    
    # 处理窗口的放缩
    def _custom_resize_event(self, event):
        self.resizeEvent_orig(event)
        if self._current_background_path: # 如果有当前背景路径
            # 从原始路径重新加载和缩放图片质量应该会更优一些
            self._set_background_from_path(self._current_background_path)
        else:
            # 检查当前是否已设置背景画刷
            palette = self.palette() #返回调色板对象（管理控件的各种颜色和画刷
            brush = palette.brush(QPalette.Window) #返回窗口背景角色的画刷
            if brush.style() != Qt.NoBrush and brush.texture().isNull() is False: #判断是否设置了背景图片
                pixmap = brush.texture() # 获取当前的像素图对象
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
                    self.setPalette(palette)
    
    def _save_background_setting(self):
        """将当前背景图片路径保存到JSON配置文件"""
        if not self.background_config_path:
            print("错误: 配置文件路径未设置，无法保存背景。")
            return

        settings = {}
        settings['background_image_path'] = self._current_background_path
        try:
            # 确保配置文件所在的目录存在
            os.makedirs(os.path.dirname(self.background_config_path), exist_ok=True)
            with open(self.background_config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            print(f"背景设置已保存到: {self.background_config_path}")
        except Exception as e:
            print(f"错误: 无法保存背景设置到 {self.background_config_path}: {e}")
    
    def _load_background_setting_path(self):
        """从JSON配置文件加载背景图片路径"""
        if not self.background_config_path or not os.path.exists(self.background_config_path):
            print(f"配置文件不存在或路径无效: {self.background_config_path}。将使用默认背景。")
            return None
        try:
            with open(self.background_config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('background_image_path')
        except Exception as e:
            print(f"错误: 无法加载背景设置从 {self.background_config_path}: {e}")
            return None
    def set_hovered_pin(self, pin_item):
        """设置当前悬停的引脚"""
        if hasattr(self, 'hovered_pin'):
            self.hovered_pin.set_hovered(False)
        self.hovered_pin = pin_item
        pin_item.set_hovered(True)
        self.voltage_label.setText(f"悬停引脚: {pin_item.node_name} 电压: {pin_item.get_voltage():.2f} V")

    def clear_hovered_pin(self):
        """清除当前悬停的引脚"""
        if hasattr(self, 'hovered_pin'):
            self.hovered_pin.set_hovered(False)
            self.hovered_pin = None
        self.voltage_label.setText("悬停引脚查看电压")

    def undo_command(self):
        """撤销命令"""
        if self.command_manager.undo():
            desc = self.command_manager.get_undo_description()
            self.statusBar().showMessage(f"已撤销: {desc if desc else '操作'}")
        else:
            self.statusBar().showMessage("没有可撤销的操作")

    def redo_command(self):
        """重做命令"""
        if self.command_manager.redo():
            desc = self.command_manager.get_redo_description()
            self.statusBar().showMessage(f"已重做: {desc if desc else '操作'}")
        else:
            self.statusBar().showMessage("没有可重做的操作")

    def delete_selected(self):
        """删除选中的元件或连线"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            self.statusBar().showMessage("没有选中的项目")
            return
        
        deleted_count = 0
        for item in selected_items:
            # 检查是否是 GraphicComponentItem
            if hasattr(item, 'spice_type') and hasattr(item, 'name'):  # 元件
                command = RemoveComponentCommand(self.scene, item)
                self.command_manager.execute_command(command)
                deleted_count += 1
            # 检查是否是 WireItem
            elif hasattr(item, 'start_pin') and hasattr(item, 'end_pin'):  # 连线
                command = RemoveWireCommand(self.scene, item)
                self.command_manager.execute_command(command)
                deleted_count += 1
        
        if deleted_count > 0:
            self.statusBar().showMessage(f"已删除 {deleted_count} 个项目")
            self._set_saved(False)
        else:
            self.statusBar().showMessage("没有可删除的项目")

    def add_wire_with_command(self, wire_item):
        """使用命令管理器添加连线"""
        command = AddWireCommand(self.scene, wire_item)
        self.command_manager.execute_command(command)
        self._set_saved(False)

    def remove_wire_with_command(self, wire_item):
        """使用命令管理器删除连线"""
        command = RemoveWireCommand(self.scene, wire_item)
        self.command_manager.execute_command(command)
        self._set_saved(False)

    # 恢复标准输出流和标准错误输出流，防止主应用退出后的python代码出错
    def closeEvent(self, event):
        sys.stdout = sys.__stdout__ 
        sys.stderr = sys.__stderr__
        super().closeEvent(event)
        self._set_saved(False)
