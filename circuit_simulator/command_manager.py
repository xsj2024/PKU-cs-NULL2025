from abc import ABC, abstractmethod
from PyQt5.QtCore import QPointF
import copy

class Command(ABC):
    """命令基类，实现命令模式"""
    @abstractmethod
    def execute(self):
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self):
        """撤销命令"""
        pass
    
    @abstractmethod
    def description(self):
        """命令描述"""
        pass

class AddComponentCommand(Command):
    """添加元件命令"""
    def __init__(self, scene, component_item):
        self.scene = scene
        self.component_item = component_item
        self.was_executed = False
    
    def execute(self):
        if not self.was_executed:
            self.scene.addItem(self.component_item)
            if self.component_item not in self.scene.components:
                self.scene.components.append(self.component_item)
            self.was_executed = True
    
    def undo(self):
        if self.was_executed:
            self.scene.removeItem(self.component_item)
            if self.component_item in self.scene.components:
                self.scene.components.remove(self.component_item)
            self.was_executed = False
    
    def description(self):
        return f"添加元件 {self.component_item.name}"

class RemoveComponentCommand(Command):
    """删除元件命令"""
    def __init__(self, scene, component_item):
        self.scene = scene
        self.component_item = component_item
        self.connected_wires = []  # 保存与该元件相连的连线
        self.was_executed = False
    
    def execute(self):
        if not self.was_executed:
            # 先保存并删除与该元件相连的所有连线
            self.connected_wires = []
            for wire in self.scene.wires[:]:  # 使用切片避免修改时出错
                if (wire.start_pin and wire.start_pin.parent() == self.component_item) or \
                   (wire.end_pin and wire.end_pin.parent() == self.component_item):
                    self.connected_wires.append(wire)
                    self.scene.removeItem(wire)
                    if wire in self.scene.wires:
                        self.scene.wires.remove(wire)
            
            # 删除元件
            self.scene.removeItem(self.component_item)
            if self.component_item in self.scene.components:
                self.scene.components.remove(self.component_item)
            self.was_executed = True
    
    def undo(self):
        if self.was_executed:
            # 恢复元件
            self.scene.addItem(self.component_item)
            if self.component_item not in self.scene.components:
                self.scene.components.append(self.component_item)
            
            # 恢复连线
            for wire in self.connected_wires:
                self.scene.addItem(wire)
                if wire not in self.scene.wires:
                    self.scene.wires.append(wire)
            
            self.was_executed = False
    
    def description(self):
        return f"删除元件 {self.component_item.name}"

class MoveComponentCommand(Command):
    """移动元件命令"""
    def __init__(self, component_item, old_pos, new_pos):
        self.component_item = component_item
        self.old_pos = QPointF(old_pos)
        self.new_pos = QPointF(new_pos)
    
    def execute(self):
        self.component_item.setPos(self.new_pos)
        # 更新连接到该元件的所有连线
        self._update_connected_wires()
    
    def undo(self):
        self.component_item.setPos(self.old_pos)
        # 更新连接到该元件的所有连线
        self._update_connected_wires()
    
    def _update_connected_wires(self):
        """更新连接到该元件的所有连线"""
        scene = self.component_item.scene()
        if scene and hasattr(scene, 'wires'):
            for wire in scene.wires:
                if (wire.start_pin and wire.start_pin.parent_component == self.component_item) or \
                   (wire.end_pin and wire.end_pin.parent_component == self.component_item):
                    if hasattr(wire, 'update_path'):
                        wire.update_path()
    
    def description(self):
        return f"移动元件 {self.component_item.name}"

class AddWireCommand(Command):
    """添加连线命令"""
    
    def __init__(self, scene, wire_item):
        self.scene = scene
        self.wire_item = wire_item
        self.was_executed = False
    
    def execute(self):
        if not self.was_executed:
            self.scene.addItem(self.wire_item)
            if self.wire_item not in self.scene.wires:
                self.scene.wires.append(self.wire_item)
            
            # 更新引脚的连线列表
            if self.wire_item.start_pin:
                if self.wire_item not in self.wire_item.start_pin.connected_wires:
                    self.wire_item.start_pin.connected_wires.append(self.wire_item)
            if self.wire_item.end_pin:
                if self.wire_item not in self.wire_item.end_pin.connected_wires:
                    self.wire_item.end_pin.connected_wires.append(self.wire_item)
            
            self.was_executed = True
    
    def undo(self):
        if self.was_executed:
            self.scene.removeItem(self.wire_item)
            if self.wire_item in self.scene.wires:
                self.scene.wires.remove(self.wire_item)
            
            # 从引脚的连线列表中移除
            if self.wire_item.start_pin and self.wire_item in self.wire_item.start_pin.connected_wires:
                self.wire_item.start_pin.connected_wires.remove(self.wire_item)
            if self.wire_item.end_pin and self.wire_item in self.wire_item.end_pin.connected_wires:
                self.wire_item.end_pin.connected_wires.remove(self.wire_item)
            
            self.was_executed = False
    
    def description(self):
        return f"添加连线"

class RemoveWireCommand(Command):
    """删除连线命令"""
    
    def __init__(self, scene, wire_item):
        self.scene = scene
        self.wire_item = wire_item
        self.was_executed = False
    
    def execute(self):
        if not self.was_executed:
            self.scene.removeItem(self.wire_item)
            if self.wire_item in self.scene.wires:
                self.scene.wires.remove(self.wire_item)
            
            # 从引脚的连线列表中移除
            if self.wire_item.start_pin and self.wire_item in self.wire_item.start_pin.connected_wires:
                self.wire_item.start_pin.connected_wires.remove(self.wire_item)
            if self.wire_item.end_pin and self.wire_item in self.wire_item.end_pin.connected_wires:
                self.wire_item.end_pin.connected_wires.remove(self.wire_item)
            
            self.was_executed = True
    
    def undo(self):
        if self.was_executed:
            self.scene.addItem(self.wire_item)
            if self.wire_item not in self.scene.wires:
                self.scene.wires.append(self.wire_item)
            
            # 重新添加到引脚的连线列表
            if self.wire_item.start_pin:
                if self.wire_item not in self.wire_item.start_pin.connected_wires:
                    self.wire_item.start_pin.connected_wires.append(self.wire_item)
            if self.wire_item.end_pin:
                if self.wire_item not in self.wire_item.end_pin.connected_wires:
                    self.wire_item.end_pin.connected_wires.append(self.wire_item)
            
            self.was_executed = False
    
    def description(self):
        return f"删除连线"

class ClearSceneCommand(Command):
    """清空场景命令"""
    def __init__(self, scene):
        self.scene = scene
        self.saved_components = []
        self.saved_wires = []
        self.was_executed = False
    
    def execute(self):
        if not self.was_executed:
            # 保存当前状态
            self.saved_components = self.scene.components.copy()
            self.saved_wires = self.scene.wires.copy()
            
            # 清空场景
            self.scene.clear()
            self.scene.components = []
            self.scene.wires = []
            self.was_executed = True
    
    def undo(self):
        if self.was_executed:
            # 清空当前场景
            self.scene.clear()
            self.scene.components = []
            self.scene.wires = []
            
            # 恢复保存的状态
            for component in self.saved_components:
                self.scene.addItem(component)
                self.scene.components.append(component)
            
            for wire in self.saved_wires:
                self.scene.addItem(wire)
                self.scene.wires.append(wire)
            
            self.was_executed = False
    
    def description(self):
        return "清空场景"

class CommandManager:
    """命令管理器，实现撤销/重做功能"""
    def __init__(self, max_history=50):
        self.command_history = []  # 命令历史
        self.current_index = -1    # 当前命令索引
        self.max_history = max_history  # 最大历史记录数
        self.main_window = None    # 主窗口引用
        self.move_command_buffer = None  # 移动命令缓冲区
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
    
    def execute_command(self, command):
        """执行命令并添加到历史记录"""
        # 执行命令
        command.execute()
        
        # 如果当前不在历史记录的末尾，删除后面的命令
        if self.current_index < len(self.command_history) - 1:
            self.command_history = self.command_history[:self.current_index + 1]
        
        # 添加新命令到历史记录
        self.command_history.append(command)
        self.current_index += 1
        
        # 限制历史记录长度
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
            self.current_index -= 1
        
        # 更新主窗口的保存状态
        if self.main_window:
            self.main_window._set_saved(False)
        
        print(f"执行命令: {command.description()}")
    
    def start_move_command(self, component_item, start_pos):
        """开始移动命令（当用户开始拖动时调用）"""
        self.move_command_buffer = {
            'component': component_item,
            'start_pos': QPointF(start_pos)
        }
    
    def finish_move_command(self, component_item, end_pos):
        """完成移动命令（当用户完成拖动时调用）"""
        if (self.move_command_buffer and 
            self.move_command_buffer['component'] == component_item):
            
            start_pos = self.move_command_buffer['start_pos']
            end_pos = QPointF(end_pos)
            
            # 只有在位置真正改变时才创建命令
            if (abs(start_pos.x() - end_pos.x()) > 1 or 
                abs(start_pos.y() - end_pos.y()) > 1):
                
                move_command = MoveComponentCommand(component_item, start_pos, end_pos)
                self.execute_command(move_command)
            
            self.move_command_buffer = None
    
    def undo(self):
        """撤销最后一个命令"""
        if self.can_undo():
            command = self.command_history[self.current_index]
            command.undo()
            self.current_index -= 1
            
            # 更新主窗口的保存状态
            if self.main_window:
                self.main_window._set_saved(False)
            
            print(f"撤销命令: {command.description()}")
            return True
        return False
    
    def redo(self):
        """重做下一个命令"""
        if self.can_redo():
            self.current_index += 1
            command = self.command_history[self.current_index]
            command.execute()
            
            # 更新主窗口的保存状态
            if self.main_window:
                self.main_window._set_saved(False)
            
            print(f"重做命令: {command.description()}")
            return True
        return False
    
    def can_undo(self):
        """检查是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self):
        """检查是否可以重做"""
        return self.current_index < len(self.command_history) - 1
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history = []
        self.current_index = -1
        self.move_command_buffer = None
        print("命令历史已清空")
    
    def get_undo_description(self):
        """获取可撤销命令的描述"""
        if self.can_undo():
            return self.command_history[self.current_index].description()
        return None
    
    def get_redo_description(self):
        """获取可重做命令的描述"""
        if self.can_redo():
            return self.command_history[self.current_index + 1].description()
        return None
    
    def get_history_info(self):
        """获取历史记录信息"""
        return {
            'total_commands': len(self.command_history),
            'current_index': self.current_index,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'undo_desc': self.get_undo_description(),
            'redo_desc': self.get_redo_description()
        }