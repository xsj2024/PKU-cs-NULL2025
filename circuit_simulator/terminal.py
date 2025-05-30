from PyQt5.QtWidgets import QPlainTextEdit,QApplication
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtCore import QObject, pyqtSignal
from ai_manager import ai_agent

class TerminalWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_start_position = 0  #记录当前输入行的起始位置
        self.command_history = [] #历史命令
        self.history_index = -1 #索引
        self.ai_model = ai_agent()

        # 设置一些基本属性
        self.setFont(QFont("Consolas", 10)) #使用等宽字体
        self.setReadOnly(False)

    # 处理按键操作
    def keyPressEvent(self, event):
        cursor = self.textCursor() #获取当前光标对象

        # 光标在只读区域
        if cursor.position() < self.input_start_position:
            # 允许导航键和复制，modifiers针对修饰键（modifiers keys）
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
                               Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End) or \
               (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C):
                super().keyPressEvent(event)
            # 如果按回车，也当作命令处理 (允许从历史记录中选择后直接回车)
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                 self._process_input_line()
            return # 阻止其他编辑操作

        # 处理可编辑区
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._process_input_line()
        elif event.key() == Qt.Key_Up:
            self._history_up()
        elif event.key() == Qt.Key_Down:
            self._history_down()
        elif event.key() == Qt.Key_Backspace:
            if cursor.position() == self.input_start_position and not cursor.hasSelection():
                return # 判断是否在提示符之后且没有选中文本，防止删除提示符
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event) #父类允许正常输入文本

    def _history_up(self):
        if self.command_history:
            if self.history_index == -1: # 第一次按上箭头
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            
            if self.history_index >= 0:
                self._set_current_input(self.command_history[self.history_index])

    def _history_down(self):
        if self.command_history and self.history_index != -1:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._set_current_input(self.command_history[self.history_index])
            else: # 到了历史记录末尾，清空当前输入
                self.history_index = -1 
                self._set_current_input("")

    def _set_current_input(self, text):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(self.input_start_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor) #保持锚点（也就上一行设置的起始位置），选中当前输入区域
        cursor.insertText(text) #替换为历史命令
        cursor.endEditBlock()
        self.setTextCursor(cursor) #确保光标在末尾

    def _process_input_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End) # 确保光标在文本末尾
        self.setTextCursor(cursor)

        # 提取当前输入行的文本
        # 从 self.input_start_position 到文档末尾
        input_text = self.toPlainText()[self.input_start_position:].strip()

        self.insertPlainText("\n") # 模拟回车换行

        if input_text:
            if not self.command_history or self.command_history[-1] != input_text:
                self.command_history.append(input_text) # 遇上一行相同的命令就不加入了
            self.history_index = -1 # 重置历史记录索引
            self.handle_ai_command(input_text)
        else:
            # 如果只是空行，也显示新提示符
            self.show_prompt()


    def show_prompt(self):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(">>> ")
        self.moveCursor(QTextCursor.End)
        self.input_start_position = self.textCursor().position()
        self.ensureCursorVisible()

    @pyqtSlot(str) # 标记为槽函数，期望接受一个字符串参数，以便从其他线程安全地调用，功能是追加文本到终端，也就是添加在提示符之前
    @pyqtSlot(str,bool) #第二个bool参数用于区分来源，以免把用户已经输入调用ai的文字再一次恢复
    def append_text(self, text,is_direct_command_output = False):
        cursor = self.textCursor() # 这时候光标位置在实际位置
        cursor.beginEditBlock()

        # 暂存当前输入
        cursor.movePosition(QTextCursor.End)
        current_input = ""
        if not is_direct_command_output:
            # 确保 self.input_start_position 是有效的，并且确实有内容在提示符后
            # 并且光标确实在 input_start_position 之后
            temp_cursor_for_check = QTextCursor(self.document()) # 创建一个临时光标来检查文档末尾
            temp_cursor_for_check.movePosition(QTextCursor.End)
            # 检查 input_start_position 是否有意义，以及当前是否有实际输入
            if self.input_start_position > 0 and temp_cursor_for_check.position() > self.input_start_position:
                current_input = self.toPlainText()[self.input_start_position:]
        
        current_block_text = cursor.block().text()
        if current_block_text[:4] == ">>> ":
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.insertBlock() # 确保新行
        elif not self.toPlainText().endswith('\n') and self.toPlainText(): #如果不是空且末尾没换行
             cursor.insertText("\n")


        cursor.insertText(text)
        if not text.endswith('\n'): # 确保输出后有换行
            cursor.insertText("\n")
        
        cursor.endEditBlock()
        self.setTextCursor(cursor) # 更新光标
        self.ensureCursorVisible() # 滚动到底部

        # 在输出后重新显示提示符
        self.show_prompt()
        if current_input:
            self.insertPlainText(current_input) #插入纯文本
            self.moveCursor(QTextCursor.End)

    def handle_ai_command(self, command):
        if not self.ai_model.usable:
            self.append_text("[System] AI is not configured or failed to load. Cannot process AI command.\n")
            return
        self.append_text(f"[AI] Processing your request: \"{command}\"...\n", True)
        QApplication.processEvents() # 允许UI更新，显示"Processing..."
        try:
            response = self.ai_model(command)
            self.append_text(f"[AI] {response}\n\n",True)
        except Exception as e:
            self.append_text(f"[AI Error] Failed to get response: {e}\n\n",True)
    

# 定义新的标准输出信号文件类
class SignallingStdout(QObject):
    text_written = pyqtSignal(str) # 定义一个携带字符串参数的信号

    def __init__(self, parent=None):
        super().__init__(parent)
    # 每个文件类对象都有一个write方法，用于向它们写入数据，这里定义write后经过重定向后print时就会调用我新的信号输出类的write函数
    def write(self, text):
        self.text_written.emit(text) # 当贝要求写入文本时发射带字符串的信号，还需在stimulation中实现连接部分，连接到这个信号的槽函数就能接受这个text

    def flush(self): # QPlainTextEdit 会自动处理刷新
        pass