import datetime
import functools
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
        self.zone = zone
        self.initUI()

    def initUI(self):
        self.setObjectName("zoneCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(zone_list_item_style())
        self.zone_name_label = self._build_name_label()
        self._build_ip_status_labels()
        self.menu_button = self._build_gear_button()
        self.subzones_container = self._build_subzones()
        self._assemble_layouts()
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

    # Крупная галочка канала с воздухом между строками — под правило
    # «крупные контролы для пожилых дежурных операторов».
    _CHANNEL_CHECK_STYLE = (
        "QCheckBox { padding: 3px; spacing: 8px; }"
        "QCheckBox::indicator { width: 20px; height: 20px; }"
    )

    def _build_subzones(self) -> QWidget:
        self.subzones_layout = QVBoxLayout()
        self.subzones_layout.setSpacing(10)
        self.subzones_layout.setContentsMargins(10, 6, 5, 4)

        container = QWidget()
        container.setLayout(self.subzones_layout)
        container.setStyleSheet("background: transparent;")
        self.subzones_container = container
        self._rebuild_subzone_checkboxes()
        return container

    def _rebuild_subzone_checkboxes(self) -> None:
        """Перестраивает интерактивные галочки active для present-каналов зоны."""
        while self.subzones_layout.count():
            item = self.subzones_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.channel_checks = {}
        for n in range(1, 9):
            if not getattr(self.zone, f"subzone{n}_present"):
                continue
            name = getattr(self.zone, f"subzone{n}_name") or f"Канал {n}"
            chk = QCheckBox(name)
            chk.setStyleSheet(self._CHANNEL_CHECK_STYLE)
            chk.setChecked(getattr(self.zone, f"subzone{n}"))
            chk.stateChanged.connect(functools.partial(self._on_channel_toggled, n))
            self.subzones_layout.addWidget(chk)
            self.channel_checks[n] = chk

    def _on_channel_toggled(self, n: int, state) -> None:
        setattr(self.zone, f"subzone{n}", state == Qt.Checked)
        self.save_zone_state()

    def _assemble_layouts(self) -> None:
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.zone.isChecked)
        self.checkbox.stateChanged.connect(self.change_checked_state)
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

        zone_info_layout = QHBoxLayout()
        zone_info_layout.addWidget(self.zone_ip_label)
        zone_info_layout.addWidget(self.online_status_label)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.checkbox, 0, Qt.AlignHCenter)
        left_layout.addWidget(self.status_indicator, 0, Qt.AlignHCenter)
        left_layout.setSpacing(4)
        left_layout.addStretch()

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.zone_name_label)
        center_layout.addLayout(zone_info_layout)
        center_layout.addWidget(self.subzones_container)
        center_layout.setSpacing(4)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.menu_button)
        right_layout.addStretch()
        right_layout.setSpacing(5)

        zone_container = QHBoxLayout()
        zone_container.addLayout(left_layout, 1)
        zone_container.addLayout(center_layout, 12)
        zone_container.addLayout(right_layout, 1)
        zone_container.setContentsMargins(10, 8, 10, 8)
        zone_container.setSpacing(8)

        self.setLayout(zone_container)

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

    def update_zone_data(self, zone: Orange):
        """Обновляет данные зоны и перерисовывает интерфейс"""
        self.zone = zone
        self._rebuild_subzone_checkboxes()
        self.checkbox.setChecked(zone.isChecked)
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
        self.save_zone_state()
        self._refresh_accents()

    def save_zone_state(self):
        try:
            with open(zones_json, 'r') as file:
                zones = json.load(file)

            for zone in zones:
                if zone['name'] == self.zone.name:
                    zone['isChecked'] = self.zone.isChecked
                    for n in range(1, 9):
                        zone[f'subzone{n}'] = getattr(self.zone, f'subzone{n}')
                        zone[f'subzone{n}_present'] = getattr(self.zone, f'subzone{n}_present')
                        zone[f'subzone{n}_name'] = getattr(self.zone, f'subzone{n}_name')

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