from abc import ABC, abstractmethod
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGraphicsItem

class Command(ABC):
    """命令基类，所有可撤回的操作都需要继承这个类"""
    
    @abstractmethod
    def execute(self):
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self):
        """撤回命令"""
        pass
    
    @abstractmethod
    def get_description(self):
        """获取命令描述"""
        pass

class AddComponentCommand(Command):
    """添加元件命令"""
    
    def __init__(self, scene, component):
        self.scene = scene
        self.component = component
        self.was_in_components = False
    
    def execute(self):
        """执行添加元件"""
        if self.component not in self.scene.items():
            self.scene.addItem(self.component)
        if self.component not in self.scene.components:
            self.scene.components.append(self.component)
            self.was_in_components = True
    
    def undo(self):
        """撤回添加元件"""
        if self.component in self.scene.items():
            self.scene.removeItem(self.component)
        if self.was_in_components and self.component in self.scene.components:
            self.scene.components.remove(self.component)
    
    def get_description(self):
        return f"添加元件 {self.component.name}"

class RemoveComponentCommand(Command):
    """删除元件命令"""
    
    def __init__(self, scene, component):
        self.scene = scene
        self.component = component
        self.position = component.pos()
        self.rotation = component.rotation()
        self.was_in_components = component in scene.components
    
    def execute(self):
        """执行删除元件"""
        if self.component in self.scene.items():
            self.scene.removeItem(self.component)
        if self.component in self.scene.components:
            self.scene.components.remove(self.component)
    
    def undo(self):
        """撤回删除元件"""
        self.component.setPos(self.position)
        self.component.setRotation(self.rotation)
        if self.component not in self.scene.items():
            self.scene.addItem(self.component)
        if self.was_in_components and self.component not in self.scene.components:
            self.scene.components.append(self.component)
    
    def get_description(self):
        return f"删除元件 {self.component.name}"

class MoveComponentCommand(Command):
    """移动元件命令"""
    
    def __init__(self, component, old_pos, new_pos):
        self.component = component
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        """执行移动元件"""
        self.component.setPos(self.new_pos)
    
    def undo(self):
        """撤回移动元件"""
        self.component.setPos(self.old_pos)
    
    def get_description(self):
        return f"移动元件 {self.component.name}"

class AddWireCommand(Command):
    """添加连线命令"""
    
    def __init__(self, scene, wire):
        self.scene = scene
        self.wire = wire
        self.was_in_wires = False
    
    def execute(self):
        """执行添加连线"""
        if self.wire not in self.scene.items():
            self.scene.addItem(self.wire)
        if self.wire not in self.scene.wires:
            self.scene.wires.append(self.wire)
            self.was_in_wires = True
    
    def undo(self):
        """撤回添加连线"""
        if self.wire in self.scene.items():
            self.scene.removeItem(self.wire)
        if self.was_in_wires and self.wire in self.scene.wires:
            self.scene.wires.remove(self.wire)
    
    def get_description(self):
        return "添加连线"

class RemoveWireCommand(Command):
    """删除连线命令"""
    
    def __init__(self, scene, wire):
        self.scene = scene
        self.wire = wire
        self.was_in_wires = wire in scene.wires
    
    def execute(self):
        """执行删除连线"""
        if self.wire in self.scene.items():
            self.scene.removeItem(self.wire)
        if self.wire in self.scene.wires:
            self.scene.wires.remove(self.wire)
    
    def undo(self):
        """撤回删除连线"""
        if self.wire not in self.scene.items():
            self.scene.addItem(self.wire)
        if self.was_in_wires and self.wire not in self.scene.wires:
            self.scene.wires.append(self.wire)
    
    def get_description(self):
        return "删除连线"

class ClearSceneCommand(Command):
    """清空场景命令"""
    
    def __init__(self, scene):
        self.scene = scene
        self.saved_items = []
        self.saved_components = []
        self.saved_wires = []
    
    def execute(self):
        """执行清空场景"""
        # 保存当前状态
        self.saved_items = list(self.scene.items())
        self.saved_components = list(self.scene.components)
        self.saved_wires = list(self.scene.wires)
        
        # 清空场景
        self.scene.clear()
        self.scene.components = []
        self.scene.wires = []
    
    def undo(self):
        """撤回清空场景"""
        # 恢复所有项目
        for item in self.saved_items:
            if item not in self.scene.items():
                self.scene.addItem(item)
        
        self.scene.components = list(self.saved_components)
        self.scene.wires = list(self.saved_wires)
    
    def get_description(self):
        return "清空场景"

class CommandManager(QObject):
    """命令管理器，管理所有的撤回/重做操作"""
    
    # 信号：当撤回/重做状态改变时发出
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)
    
    def __init__(self, max_commands=100):
        super().__init__()
        self.max_commands = max_commands
        self.commands = []  # 命令历史
        self.current_index = -1  # 当前命令索引
    
    def execute_command(self, command):
        """执行命令并加入历史"""
        command.execute()
        
        # 如果当前不在历史末尾，删除之后的命令
        if self.current_index < len(self.commands) - 1:
            self.commands = self.commands[:self.current_index + 1]
        
        # 添加新命令
        self.commands.append(command)
        self.current_index += 1
        
        # 限制命令历史长度
        if len(self.commands) > self.max_commands:
            self.commands.pop(0)
            self.current_index -= 1
        
        self._emit_state_changed()
    
    def undo(self):
        """撤回操作"""
        if self.can_undo():
            command = self.commands[self.current_index]
            command.undo()
            self.current_index -= 1
            self._emit_state_changed()
            return command.get_description()
        return None
    
    def redo(self):
        """重做操作"""
        if self.can_redo():
            self.current_index += 1
            command = self.commands[self.current_index]
            command.execute()
            self._emit_state_changed()
            return command.get_description()
        return None
    
    def can_undo(self):
        """是否可以撤回"""
        return self.current_index >= 0
    
    def can_redo(self):
        """是否可以重做"""
        return self.current_index < len(self.commands) - 1
    
    def clear(self):
        """清空命令历史"""
        self.commands.clear()
        self.current_index = -1
        self._emit_state_changed()
    
    def get_undo_text(self):
        """获取撤回操作的描述"""
        if self.can_undo():
            return f"撤回: {self.commands[self.current_index].get_description()}"
        return "撤回"
    
    def get_redo_text(self):
        """获取重做操作的描述"""
        if self.can_redo():
            return f"重做: {self.commands[self.current_index + 1].get_description()}"
        return "重做"
    
    def _emit_state_changed(self):
        """发出状态改变信号"""
        self.can_undo_changed.emit(self.can_undo())
        self.can_redo_changed.emit(self.can_redo())