from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QCheckBox, QLabel, QPushButton
from qtpy import QtCore


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()

        self.setWindowTitle('Настройка PCN')
        self.setGeometry(QtCore.QRect(900, 500, 400, 200))

        layout = QVBoxLayout()

        self.label = QLabel('Идентификатор автотеста PCN6')
        layout.addWidget(self.label)

        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText('Идентификатор для автотеста')
        layout.addWidget(self.lineEdit)

        self.checkBox = QCheckBox('Инверсия контактов сонаты')
        layout.addWidget(self.checkBox)

        self.saveButton = QPushButton('Сохранить настройки')
        layout.addWidget(self.saveButton)

        self.cancelButton = QPushButton('Отмена')
        layout.addWidget(self.cancelButton)

        self.setLayout(layout)
