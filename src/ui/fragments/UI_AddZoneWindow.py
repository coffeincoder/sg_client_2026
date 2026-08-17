from typing import List

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QPushButton,
                             QHBoxLayout, QMessageBox, QLabel, QGridLayout,
                             QCheckBox)

from src.data.ZoneModel import Orange

ip_regex = QRegExp("^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\."
                   "([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$")


class UI_AddZoneWindow(QDialog):
    def __init__(self, zone_name, ip, all_zones, channels=None, for_rename=False):
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

        # Set initial values
        self.ip_field.setText(ip)
        self.name_field.setText(zone_name)

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

        self.channel_checks = []
        self.channel_fields = []
        for i in range(4):
            chk = QCheckBox(f"Канал {i + 1}")
            fld = QLineEdit()
            fld.setPlaceholderText(f"Введите имя канала {i + 1}")
            active, name = channels[i] if channels else (False, "")
            chk.setChecked(active)
            fld.setText(name)
            fld.setEnabled(active)
            chk.toggled.connect(fld.setEnabled)
            row = 2 + i
            self.input_layout.addWidget(chk, row, 0)
            self.input_layout.addWidget(fld, row, 1)
            self.channel_checks.append(chk)
            self.channel_fields.append(fld)

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

    def set_name_field_text(self, name: str):
        self.name_field.setText(name)

    def set_ip_field_text(self, ip: str):
        self.ip_field.setText(ip)

    def get_channels(self) -> List[tuple]:
        return [(c.isChecked(), f.text()) for c, f in zip(self.channel_checks, self.channel_fields)]