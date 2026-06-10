from typing import List

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QMessageBox, QLabel, QGridLayout)

from src.data.ZoneModel import Orange

ip_regex = QRegExp("^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\."
                   "([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$")


class UI_AddZoneWindow(QDialog):
    def __init__(self, zone_name, ip, all_zones, channel1="", channel2="", for_rename=False):
        super().__init__()
        self.all_zones: List[Orange] = all_zones
        self.setMinimumWidth(350)
        self.for_rename = for_rename

        self.main_layout = QVBoxLayout()
        self.input_layout = QGridLayout()  # Изменено на QGridLayout для лучшего выравнивания
        self.buttons_layout = QHBoxLayout()

        self.setWindowTitle("Добавление новой зоны")

        ip_validator = QRegExpValidator(ip_regex, self)

        # Name field with label
        self.name_label = QLabel("Название зоны:")
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Введите название зоны")

        # IP address field with label
        self.ip_label = QLabel("IP адрес:")
        self.ip_field = QLineEdit()
        self.ip_field.setValidator(ip_validator)
        self.ip_field.setPlaceholderText("Введите IP адрес")

        # Channel 1 field with label
        self.channel1_label = QLabel("Канал 1:")
        self.channel1_field = QLineEdit()
        self.channel1_field.setPlaceholderText("Введите канал 1")

        # Channel 2 field with label
        self.channel2_label = QLabel("Канал 2:")
        self.channel2_field = QLineEdit()
        self.channel2_field.setPlaceholderText("Введите канал 2")

        # Set initial values
        self.ip_field.setText(ip)
        self.name_field.setText(zone_name)
        self.channel1_field.setText(channel1)
        self.channel2_field.setText(channel2)

        # Buttons
        button_ok = QPushButton("сохранить")
        button_ok.clicked.connect(self.validate_and_accept)

        button_cancel = QPushButton("отмена")
        button_cancel.clicked.connect(self.reject)

        button_ok.setFixedHeight(30)
        button_cancel.setFixedHeight(30)

        # Add widgets to grid layout with labels
        self.input_layout.addWidget(self.name_label, 0, 0)
        self.input_layout.addWidget(self.name_field, 0, 1)

        self.input_layout.addWidget(self.ip_label, 1, 0)
        self.input_layout.addWidget(self.ip_field, 1, 1)

        self.input_layout.addWidget(self.channel1_label, 2, 0)
        self.input_layout.addWidget(self.channel1_field, 2, 1)

        self.input_layout.addWidget(self.channel2_label, 3, 0)
        self.input_layout.addWidget(self.channel2_field, 3, 1)

        self.buttons_layout.addWidget(button_ok)
        self.buttons_layout.addWidget(button_cancel)

        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addLayout(self.buttons_layout)

        self.setLayout(self.main_layout)

    def validate_and_accept(self):
        if self.for_rename:
            self.accept()
        elif self.ip_field.text() != '' or self.name_field.text() != '':
            if any(zone.name == self.name_field.text() for zone in self.all_zones):
                QMessageBox.information(self, 'Уведомление.', 'Зона с таким названием уже существует!')
                return
            self.accept()

    def get_name_field(self) -> QLineEdit:
        return self.name_field

    def get_ip_field(self) -> QLineEdit:
        return self.ip_field

    def get_channel1_field(self) -> QLineEdit:
        return self.channel1_field

    def get_channel2_field(self) -> QLineEdit:
        return self.channel2_field

    def set_name_field_text(self, name: str):
        self.name_field.setText(name)

    def set_ip_field_text(self, ip: str):
        self.ip_field.setText(ip)

    def set_channel1_field_text(self, channel1: str):
        self.channel1_field.setText(channel1)

    def set_channel2_field_text(self, channel2: str):
        self.channel2_field.setText(channel2)

    def get_channel1_text(self) -> str:
        return self.channel1_field.text()

    def get_channel2_text(self) -> str:
        return self.channel2_field.text()