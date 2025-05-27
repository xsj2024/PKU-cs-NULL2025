from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLabel
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtCore import Qt, QDir,QFileInfo

class BackgroundDialog(QDialog):
    def __init__(self, parent_window, default_images=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setWindowTitle("设置背景图片")
        self.setGeometry(100, 100, 700, 400)
        self.layout = QVBoxLayout(self)

        self.image_list = QListWidget()
        self.default_images = default_images if default_images else []
        for img_path in self.default_images:
            # 检查路径有效性，只添加存在的图片
            if QFileInfo(img_path).exists():
                self.image_list.addItem(img_path)
            else:
                print(f"警告: 默认图片路径无效，未添加到列表: {img_path}")
        self.image_list.addItem("自定义...")
        self.layout.addWidget(self.image_list)

        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self.apply_background)
        self.layout.addWidget(self.apply_button)

        self.image_list.itemClicked.connect(self.preview_or_select)
        self.selected_image_path = None

    def preview_or_select(self, item):
        text = item.text()
        if text == "自定义...":
            self.selected_image_path = None
            self.upload_image()
        else:
            self.selected_image_path = text

    def upload_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择背景图片", "","图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)", options=options)
        if fileName:
            self.selected_image_path = fileName
            #将用户上传的图片临时添加到列表中
            if not self.image_list.findItems(fileName, Qt.MatchExactly):
                self.image_list.insertItem(self.image_list.count() -1, fileName) #插在“自定义”之前
            self.image_list.setCurrentRow(self.image_list.count() - 2)
            print(f"用户选择了: {fileName}")

    def apply_background(self):
        if self.selected_image_path:
            # 调用父窗口的方法来设置背景
            if self.parent_window._set_background_from_path(self.selected_image_path):
                self.accept()  # 如果成功设置背景，则关闭对话框
            else:
                #在对话框中向用户显示错误消息
                print("在 BackgroundDialog 中应用背景失败。主窗口未能设置背景。")
        else:
            print("没有选择图片")

