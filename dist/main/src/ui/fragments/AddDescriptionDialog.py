from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialog

from src.data.FileModel import FileItem


class AddDescriptionDialog(QDialog):
    def __init__(self, file_item: FileItem, parent=None):
        super().__init__()

        self.main_layout = QVBoxLayout()

        self.text_layout = QHBoxLayout()

        self.buttons_layout = QHBoxLayout()

        self.setWindowTitle("Ведите новое описание файла")
        self.file_item = file_item

        self.text_edit = QLineEdit()
        self.text_edit.setText(file_item.text)
        self.text_edit.setFixedHeight(30)
        f = self.text_edit.font()
        f.setPointSize(13)  # sets the size to 27
        self.text_edit.setFont(f)
        self.setMinimumWidth(640)

        button_ok = QPushButton("сохранить")
        button_ok.clicked.connect(self.accept)

        button_cancel = QPushButton("отмена")

        button_ok.setFixedHeight(30)
        button_cancel.setFixedHeight(30)
        button_cancel.clicked.connect(self.reject)

        self.main_layout.addLayout(self.text_layout, 2)
        self.main_layout.addLayout(self.buttons_layout, 1)

        self.text_layout.addWidget(self.text_edit)

        self.buttons_layout.addWidget(button_ok)
        self.buttons_layout.addWidget(button_cancel)

        self.setLayout(self.main_layout)
        self.layout().addChildLayout(self.main_layout)

    def get_text(self):
        return self.text_edit.text()
