import json
import os
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt

class shortcutManager(QObject):

    def __init__(self,parent_window):
        super().__init__()
        #初始化父窗口，将快捷键限制在父窗口中并管理生命周期
        self.parent_window = parent_window
        #快捷键对象字典
        self.shortcuts = {}
        #快捷键路径设置
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shortcuts.json")#使用绝对路径，相对路径就炸了
        #系统默认快捷键设置
        self.default_shortcuts = {
            "new_file": "Ctrl+N",
            "save_file": "Ctrl+S",
            "open_file": "Ctrl+O",
            "add_resistor": "Ctrl+Shift+R",
            #"add_capacitor": "Ctrl+Shift+C", 电容部分暂未实现
            "add_voltage": "Ctrl+Shift+V",
            "add_gnd": "Ctrl+Shift+G",
            "run_spice_simulation": "F6",
            "clear_scene": "Ctrl+E"
        }
        #当前快捷键配置
        self.current_shortcuts = {}
        #加载快捷键配置
        self.load_shortcuts()
    
    def load_shortcuts(self):
        self.current_shortcuts = self.default_shortcuts.copy()
        if os.path.exists(self.config_file):
            #读取配置文件
            with open(self.config_file,'r',encoding='utf-8') as f:
                user_shortcuts = json.load(f)
            #合并配置文件和默认设置
            self.current_shortcuts.update(user_shortcuts)
    
    def save_shortcuts(self):
        try:
            with open(self.config_file,'w',encoding='utf-8') as f:
                json.dump(self.current_shortcuts,f,indent = 4,ensure_ascii=False) #暂时预留中文快捷键名称的可能性
            print("快捷键配置更新成功")
            return True
        except Exception as e:
            print(f"快捷键配置失败:{e}")
            return False
    
    def register_a_shortcut(self,action_name,callback_function):
        key_sequence = self.current_shortcuts.get(action_name)
        if not key_sequence:
            print(f"未找到快捷键配置：{action_name}")
            return False
        try:
            #清理旧的快捷键对象
            if action_name in self.shortcuts:
                old_shortcut = self.shortcuts[action_name]
                old_shortcut.setParent(None)#断开链接
                del self.shortcuts[action_name]
            # 新的快捷键对象
            shortcut = QShortcut(QKeySequence(key_sequence), self.parent_window, context=Qt.ApplicationShortcut)#创建一个快捷键监听器，监听主窗口的按键，QKeySequence将文字转换为pyqt5能理解的按键对象
            # 链接信号与槽函数
            shortcut.activated.connect(callback_function)
            self.shortcuts[action_name] = shortcut
            return True
        except Exception as e:
            print(f"快捷键注册失败{action_name}:{e}")
            return False
    
    def register_all_shortcuts(self,callback_dict):
        print(f"正在注册 {len(callback_dict)} 个快捷键...")  # 调试输出
        for action_name, callback_function in callback_dict.items():
            success = self.register_a_shortcut(action_name, callback_function)
            print(f"快捷键 {action_name} 注册{'成功' if success else '失败'}") # 调试输出

    def show_settings_dialog(self):
        dialog = shortcutSettingDialog(self, self.parent_window)
        dialog.exec_()

class shortcutSettingDialog(QDialog):
    
    def __init__(self,shortcut_manager,parent = None):
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        # 对话框基本设置
        self.setWindowTitle("快捷键设置")
        self.setModal(True)  # 模态对话框,必须先关闭才能操作其他窗口
        self.resize(500, 400)

        self.create_ui()
        self.load_shortcuts()

    def create_ui(self):
        layout = QVBoxLayout()

        # 创建快捷键对应表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["功能", "快捷键"])

        # 设置表格属性
        self.table.setAlternatingRowColors(True)  # 交替行颜色
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        
        # 双击编辑快捷键
        self.table.itemDoubleClicked.connect(self.edit_shortcut)
        
        layout.addWidget(self.table)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 重置按钮
        reset_btn = QPushButton("重置为默认")
        reset_btn.clicked.connect(self.reset_shortcuts)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()  # 添加弹性空间
        
        # 确定和取消按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_and_close)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_shortcuts(self):
        shortcuts = self.shortcut_manager.current_shortcuts
        self.table.setRowCount(len(shortcuts))
        
        for row, (action_name, key_sequence) in enumerate(shortcuts.items()):
            # 功能名称（转换为用户友好的名称）
            display_name = self.get_display_name(action_name)
            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.UserRole, action_name)  # 存储原始名称
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 只读
            
            # 快捷键
            shortcut_item = QTableWidgetItem(key_sequence)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, shortcut_item)
    
    #内部名称改为用户看到的名称
    def get_display_name(self, action_name):

        display_names = {
            "new_file": "新建文件",
            "save_file": "保存文件",
            "open_file": "打开文件",
            "add_resistor":"添加电阻",
            #"add_capacitor": "添加电容", 电容部分暂未实现
            "add_voltage": "添加电源",
            "add_gnd": "添加接地",
            "run_spice_simulation": "运行仿真",
            "clear_scene": "清除电路"
        }
        return display_names.get(action_name, action_name) # 没找到就返回原始输入的action_name
    
    def edit_shortcut(self, item):
        """编辑快捷键"""
        # 只允许编辑快捷键列
        if item.column() != 1:
            return
        
        # 获取当前行的功能名称
        name_item = self.table.item(item.row(), 0)
        action_name = name_item.data(Qt.UserRole)
        display_name = name_item.text()
        
        # 获取当前快捷键
        current_shortcut = item.text()
        
        # 弹出输入对话框
        new_shortcut, ok = QInputDialog.getText(
            self,
            "编辑快捷键",
            f"请输入'{display_name}'的新快捷键:\n(例如: Ctrl+N, F1, Alt+S)",
            text=current_shortcut
        )
        
        if ok and new_shortcut != current_shortcut:
            # 检查快捷键是否有效
            if self.validate_shortcut(new_shortcut):
                # 检查快捷键冲突
                if self.check_conflict(action_name, new_shortcut):
                    # 更新表格
                    item.setText(new_shortcut)
                    print(f"快捷键已修改: {action_name} = {new_shortcut}")
                else:
                    QMessageBox.warning(self, "快捷键冲突", f"快捷键 '{new_shortcut}' 已被其他功能使用！")
            else:
                QMessageBox.warning(self, "无效快捷键", f"'{new_shortcut}' 不是有效的快捷键格式！")
    
    def validate_shortcut(self, shortcut_text):
        try:
            QKeySequence(shortcut_text)
            return True
        except:
            return False
    
    def check_conflict(self, current_action, new_shortcut):
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            shortcut_item = self.table.item(row, 1)
            
            other_action = name_item.data(Qt.UserRole)
            other_shortcut = shortcut_item.text()
            
            # 如果不是当前正在编辑的项，且快捷键相同
            if other_action != current_action and other_shortcut == new_shortcut:
                return False
        
        return True
    
    def reset_shortcuts(self):
        """重置为默认快捷键"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有快捷键为默认设置吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置为默认
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 0)
                shortcut_item = self.table.item(row, 1)
                
                action_name = name_item.data(Qt.UserRole)
                default_shortcut = self.shortcut_manager.default_shortcuts.get(action_name, "")
                
                shortcut_item.setText(default_shortcut)
            
            QMessageBox.information(self, "重置完成", "所有快捷键已重置为默认设置")
    
    def save_and_close(self):
        """保存设置并关闭对话框"""
        # 收集表格中的快捷键设置
        new_shortcuts = {}
        
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            shortcut_item = self.table.item(row, 1)
            
            action_name = name_item.data(Qt.UserRole)
            new_shortcut = shortcut_item.text()
            
            new_shortcuts[action_name] = new_shortcut
        
        # 更新快捷键管理器
        self.shortcut_manager.current_shortcuts = new_shortcuts
        
        # 保存到文件
        if self.shortcut_manager.save_shortcuts():
            QMessageBox.information(self, "保存成功", "快捷键设置已保存！\n重启程序后生效。")
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "无法保存快捷键设置！")