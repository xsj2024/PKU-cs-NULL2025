from openai import OpenAI
import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QPushButton, QMessageBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
class ai_agent:
    def __init__(self):
        self.API_KEY = None
        self.model_name = None
        self.temperature = None
        self.system_prompt = None
        self.client = None
        self.usable = self._load_ai_config()
        
    def __call__(self,user_prompt):
        all_response = self.client.chat.completions.create(
            model = self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            stream = False,
            temperature = self.temperature
        )
        info = all_response.choices[0].message.content
        return info
    
    def _load_ai_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'ai_Info.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.API_KEY = config.get("api_key")
            self.model_name = config.get("model_name", "deepseek-chat")
            self.temperature = config.get("temperature", 0.1)
            self.system_prompt = config.get("system_prompt", "你是一个集成在电路模拟器终端中的有用的人工智能助手。请提供简洁且相关的信息。")
            if not self.API_KEY:
                return False
            self.client = OpenAI(api_key = self.API_KEY, base_url = "https://api.deepseek.com")
            return True
        except Exception as e:
            return False

class AiConfigDialog(QDialog):
    DEFAULT_CONFIG = {
        "api_key": "YOUR_DEEPSEEK_API_KEY_HERE",
        "model_name": "deepseek-chat",
        "temperature": 0.1,
        "system_prompt": "你是一个集成在电路模拟器终端中的有用的人工智能助手。请提供简洁且相关的信息。"
    }

    def __init__(self, config_file_path, parent=None):
        super().__init__(parent)
        self.config_file_path = config_file_path
        self.setWindowTitle("AI 配置")
        self.setMinimumWidth(500)

        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入你的 DeepSeek API 密钥")
        form_layout.addRow(QLabel("API 密钥:"), self.api_key_edit)

        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("例如：deepseek-chat")
        form_layout.addRow(QLabel("模型名称:"), self.model_name_edit)

        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setValue(0.1) # 默认值
        form_layout.addRow(QLabel("温度 (Temperature):"), self.temperature_spinbox)

        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlaceholderText("描述AI的角色或个性。")
        self.system_prompt_edit.setMinimumHeight(80)
        form_layout.addRow(QLabel("系统提示 (System Prompt):"), self.system_prompt_edit)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox()
        self.reset_button = button_box.addButton("恢复默认设置", QDialogButtonBox.ResetRole)
        button_box.addButton(QDialogButtonBox.Ok)
        button_box.addButton(QDialogButtonBox.Cancel)

        button_box.accepted.connect(self._save_config_and_accept)
        button_box.rejected.connect(self.reject)
        self.reset_button.clicked.connect(self._reset_to_defaults)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def _load_config(self):
        current_config = {}
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "配置加载错误",
                                    f"无法解析 '{os.path.basename(self.config_file_path)}'。将加载默认设置。")
                current_config = self.DEFAULT_CONFIG.copy() # 如果文件损坏，则在UI中加载默认值
            except Exception as e:
                QMessageBox.warning(self, "配置加载错误",
                                    f"加载AI配置时出错: {e}。将加载默认设置。")
                current_config = self.DEFAULT_CONFIG.copy()
        else:
            # 如果文件不存在，使用默认值填充UI，但暂不显示错误，
            # 因为保存时会创建它。
            current_config = self.DEFAULT_CONFIG.copy()

        self.api_key_edit.setText(current_config.get("api_key", self.DEFAULT_CONFIG["api_key"]))
        self.model_name_edit.setText(current_config.get("model_name", self.DEFAULT_CONFIG["model_name"]))
        self.temperature_spinbox.setValue(float(current_config.get("temperature", self.DEFAULT_CONFIG["temperature"])))
        self.system_prompt_edit.setPlainText(current_config.get("system_prompt", self.DEFAULT_CONFIG["system_prompt"]))

    def _save_config_and_accept(self):
        config_to_save = {
            "api_key": self.api_key_edit.text().strip(),
            "model_name": self.model_name_edit.text().strip(),
            "temperature": self.temperature_spinbox.value(),
            "system_prompt": self.system_prompt_edit.toPlainText().strip()
        }

        if not config_to_save["api_key"] or config_to_save["api_key"] == "YOUR_DEEPSEEK_API_KEY_HERE":
            QMessageBox.warning(self, "API 密钥缺失", "请输入有效的 API 密钥。")
            return

        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "配置已保存",
                                    f"AI 配置已保存至 '{os.path.basename(self.config_file_path)}'。\n"
                                    "请重启应用程序以使更改对AI代理完全生效。")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"无法保存AI配置: {e}")

    def _reset_to_defaults(self):
        reply = QMessageBox.question(self, "重置确认",
                                     "您确定要将所有AI设置恢复为默认值吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.api_key_edit.setText(self.DEFAULT_CONFIG["api_key"])
            self.model_name_edit.setText(self.DEFAULT_CONFIG["model_name"])
            self.temperature_spinbox.setValue(self.DEFAULT_CONFIG["temperature"])
            self.system_prompt_edit.setPlainText(self.DEFAULT_CONFIG["system_prompt"])
            QMessageBox.information(self, "重置完成", "字段已恢复为默认值。点击“确定”以保存。")