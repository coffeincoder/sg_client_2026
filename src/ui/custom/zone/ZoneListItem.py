import datetime
import json
import logging
import os.path

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QToolButton, QMenu, QAction

from paths import img_files, zones_json
from src.data.ZoneModel import Orange

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QFont

from src.ui.style_sheets import list_widget_header_style, zone_list_item_style, blue_color_btn, zone_item_btn, _get_theme
from src.ui.theme import tokens_for

logger = logging.getLogger(__name__)


class ZoneListItem(QWidget):
    """Представление отдельно взятого элемента списка внутри [ZoneListWidget]"""
    delete_clicked = pyqtSignal(Orange)
    rename_clicked = pyqtSignal(Orange)

    def __init__(self, zone: Orange):
        super().__init__()
        self.menu_button = QToolButton()
        self.zone = zone

        self.setMinimumHeight(140)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.change_checked_state)
        self.zone_info_layout = QHBoxLayout()
        self.zone_name_layout = QHBoxLayout()
        self.zone_name_label = QLabel(self.zone.name)
        self.center_layout = QVBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.zone_container = QHBoxLayout()

        self.initUI()

    def initUI(self):
        self.setObjectName("zoneCard")  # облик карточки — общий QSS (src/ui/theme.py)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(zone_list_item_style())

        # Настройка основных элементов
        self.zone_name_label = self._build_name_label()

        self._build_ip_status_labels()

        # Настройка чекбоксов подзон с названиями из репозитория
        self.subzones_container = self._build_subzones()

        # Главный чекбокс зоны
        self.checkbox.setChecked(self.zone.isChecked)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
            }
            QCheckBox {
                padding: 2px;
                spacing: 5px;
            }
        """)

        # Меню действий (шестерёнка): переименование и удаление спрятаны,
        # чтобы зону нельзя было снести случайным кликом.
        self.menu_button = self._build_gear_button()

        # Компоновка элементов
        self.zone_info_layout.addWidget(self.zone_ip_label)
        self.zone_info_layout.addWidget(self.online_status_label)

        self.left_layout.addWidget(self.checkbox, 1)
        self.left_layout.addWidget(self.status_indicator, 1)
        self.left_layout.setSpacing(10)

        self.center_layout.addWidget(self.zone_name_label)
        self.center_layout.addLayout(self.zone_info_layout)
        self.center_layout.addWidget(self.subzones_container)
        self.center_layout.setSpacing(8)

        self.right_layout.addWidget(self.menu_button)
        self.right_layout.addStretch()
        self.right_layout.setSpacing(5)

        self.zone_container.addLayout(self.left_layout, 1)
        self.zone_container.addLayout(self.center_layout, 12)
        self.zone_container.addLayout(self.right_layout, 1)
        self.zone_container.setContentsMargins(14, 12, 14, 12)
        self.zone_container.setSpacing(12)

        self.setLayout(self.zone_container)
        self._refresh_accents()

    def _build_name_label(self) -> QLabel:
        label = QLabel(self.zone.name)
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setAlignment(Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        label.setWordWrap(True)
        label.setStyleSheet(list_widget_header_style())
        return label

    def _build_ip_status_labels(self) -> None:
        self.zone_ip_label = QLabel(self.zone.ip)
        self.zone_ip_label.setFont(QFont("Arial", 9))
        self.zone_ip_label.setAlignment(Qt.AlignLeft)

        self.online_status_label = QLabel("Онлайн" if self.zone.is_online else "Не в сети")
        self.online_status_label.setFont(QFont("Arial", 9))
        self.online_status_label.setAlignment(Qt.AlignRight)

        self.status_indicator = QLabel()
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setStyleSheet("QLabel { padding: 2px; }")
        self.update_status_indicator()

    def _build_gear_button(self) -> QToolButton:
        btn = QToolButton()
        btn.setIcon(QIcon(f"{img_files}{os.sep}ic-gear.png"))
        btn.setIconSize(QSize(22, 22))
        btn.setFixedSize(44, 40)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setAutoRaise(True)
        btn.setStyleSheet(zone_item_btn())

        zone_menu = QMenu(self)
        rename_action = QAction("Переименовать", self)
        delete_action = QAction("Удалить", self)
        rename_action.triggered.connect(self.rename_zone)
        delete_action.triggered.connect(self.delete_zone)
        zone_menu.addAction(rename_action)
        zone_menu.addAction(delete_action)
        btn.setMenu(zone_menu)
        return btn

    def _build_subzones(self) -> QWidget:
        subzone_style = """
            QCheckBox {
                font-size: 11px;
                padding: 4px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        self.subzone1_checkbox = QCheckBox(self.zone.subzone1_name or "Подзона 1")
        self.subzone2_checkbox = QCheckBox(self.zone.subzone2_name or "Подзона 2")

        self.subzone1_checkbox.setStyleSheet(subzone_style)
        self.subzone2_checkbox.setStyleSheet(subzone_style)
        self.subzone1_checkbox.setChecked(self.zone.subzone1)
        self.subzone2_checkbox.setChecked(self.zone.subzone2)
        self.subzone1_checkbox.setEnabled(self.zone.isChecked)
        self.subzone2_checkbox.setEnabled(self.zone.isChecked)

        self.subzone1_checkbox.stateChanged.connect(self.update_subzone1_state)
        self.subzone2_checkbox.stateChanged.connect(self.update_subzone2_state)

        layout = QVBoxLayout()
        layout.addWidget(self.subzone1_checkbox)
        layout.addWidget(self.subzone2_checkbox)
        layout.addStretch()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 5, 5, 5)

        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet("background: transparent;")
        return container

    def _refresh_accents(self):
        """Акценты: цветной статус, приглушённый IP, акцентная грань у выбранной зоны."""
        t = tokens_for(_get_theme())
        if self.zone.is_playing:
            color, text = t.accent, "Играет"
        elif self.zone.is_streaming:
            color, text = t.accent, "Вещание"
        elif self.zone.is_sip_running:
            color, text = t.accent, "Звонок"
        elif self.zone.is_online:
            color, text = t.online, "Онлайн"
        else:
            color, text = t.muted, "Не в сети"
        self.online_status_label.setText(text)
        self.online_status_label.setStyleSheet(f"color: {color}; font-weight: 600; background: transparent;")
        self.zone_ip_label.setStyleSheet(f"color: {t.muted}; background: transparent;")
        if self.zone.isChecked:
            self.setStyleSheet(
                f"QWidget#zoneCard {{ background: {t.card}; border: 1px solid {t.border};"
                f" border-left: 3px solid {t.accent}; border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet("")

    def update_subzone_labels(self):
        """Обновляет названия подзон из данных зоны"""
        self.subzone1_checkbox.setText(self.zone.subzone1_name or "Подзона 1")
        self.subzone2_checkbox.setText(self.zone.subzone2_name or "Подзона 2")

    def update_zone_data(self, zone: Orange):
        """Обновляет данные зоны и перерисовывает интерфейс"""
        self.zone = zone
        self.update_subzone_labels()
        self.checkbox.setChecked(zone.isChecked)
        self.subzone1_checkbox.setChecked(zone.subzone1)
        self.subzone2_checkbox.setChecked(zone.subzone2)
        self.subzone1_checkbox.setEnabled(zone.isChecked)
        self.subzone2_checkbox.setEnabled(zone.isChecked)
        self.online_status_label.setText("Онлайн" if zone.is_online else "Не в сети")
        self.zone_ip_label.setText(zone.ip)
        self.zone_name_label.setText(zone.name)
        self.update_status_indicator()
        self._refresh_accents()

    def update_status_indicator(self):
        if self.zone.is_playing:
            pixmap = QPixmap(os.path.join(img_files, "cast-audio-custom (1).png"))
            self.status_indicator.setToolTip(self.zone.tooltip_message)
        elif self.zone.is_streaming:
            pixmap = QPixmap(os.path.join(img_files, "microphone.png"))
        elif self.zone.is_sip_running:
            pixmap = QPixmap(os.path.join(img_files, "phone-in-talk-custom.png"))
        elif self.zone.is_warning:
            pixmap = QPixmap(os.path.join(img_files, "alert-circle-custom.png"))
            self.status_indicator.setToolTip(self.zone.tooltip_warn_message)
        else:
            if self.zone.is_online:
                pixmap = QPixmap(os.path.join(img_files, "circle-green.png"))
            else:
                pixmap = QPixmap(os.path.join(img_files, "circle-grey.png"))

        pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.status_indicator.setPixmap(pixmap)

    def change_checked_state(self, state):
        self.zone.isChecked = state == Qt.Checked
        # Только включаем/выключаем чекбоксы подзон, не сбрасывая их состояние
        self.subzone1_checkbox.setEnabled(self.zone.isChecked)
        self.subzone2_checkbox.setEnabled(self.zone.isChecked)
        self.save_zone_state()
        self._refresh_accents()

    def update_subzone1_state(self, state):
        self.zone.subzone1 = state == Qt.Checked
        self.save_zone_state()

    def update_subzone2_state(self, state):
        self.zone.subzone2 = state == Qt.Checked
        self.save_zone_state()

    def save_zone_state(self):
        try:
            with open(zones_json, 'r') as file:
                zones = json.load(file)

            for zone in zones:
                if zone['name'] == self.zone.name:
                    zone['isChecked'] = self.zone.isChecked
                    zone['subzone1'] = self.zone.subzone1
                    zone['subzone2'] = self.zone.subzone2
                    zone['subzone1_name'] = self.zone.subzone1_name
                    zone['subzone2_name'] = self.zone.subzone2_name

            with open(zones_json, 'w') as file:
                json.dump(zones, file, indent=4)

            logger.info(f"Zone state saved: {self.zone.name}")
        except Exception as e:
            logger.error(f"Error saving zone state: {str(e)}")

    def rename_zone(self):
        logger.info(f"Rename clicked: {self.zone.name}")
        self.rename_clicked.emit(self.zone)

    def delete_zone(self):
        logger.info(f"Delete clicked: {self.zone.name}")
        self.delete_clicked.emit(self.zone)