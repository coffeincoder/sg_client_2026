from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QToolButton, QAction, QMenu,
                             QPushButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

from paths import sep
from src.data.FileModel import FileItem
from src.ui.custom.ScrollLabel import ScrollLabel
from src.ui.style_sheets import *
from src.ui.style_sheets import _get_theme
from src.ui.theme import tokens_for


class FileListItem(QWidget):
    """Представление отдельно взятого элемента списка внутри [FileListWidget]"""
    rename_clicked = pyqtSignal(FileItem)
    delete_clicked = pyqtSignal(FileItem)
    listen_clicked = pyqtSignal(FileItem)
    add_description_clicked = pyqtSignal(FileItem)

    def __init__(self, file_item: FileItem, theme):
        super().__init__()
        self.theme = theme
        self.file_item = file_item
        self.initUI()

    def initUI(self):
        # Создайте рамку
        self.file_item_container = QVBoxLayout()
        self.setObjectName("fileCard")  # облик карточки — общий QSS (src/ui/theme.py)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(file_list_item_style())

        self.menu_button = QToolButton(self)
        self.menu_button.setStyleSheet(f"""
        QToolButton {{
            border-radius: 8px;
        }}
        QToolButton:hover{{
            border: 1px solid #2979FE;
            border-radius: 8px;
            background-color: transparent;
        }}
        """)

        self.menu_button.setIcon(QIcon(f"{paths.img_files}{sep}ic-gear.png"))
        self.menu_button.setIconSize(QSize(26, 26))
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setFixedSize(40, 40)

        # Создание действий для меню
        rename_action = QAction('Переименовать', self)
        delete_action = QAction('Удалить', self)
        listen_action = QAction('Прослушать', self)
        add_description = QAction('Редактировать описание', self)

        # Подключение слотов к действиям
        rename_action.triggered.connect(self.rename_file)
        listen_action.triggered.connect(self.listen_file)
        delete_action.triggered.connect(self.delete_file)
        add_description.triggered.connect(self.add_description)

        # Создание меню и добавление действий
        menu = QMenu(self)
        menu.addAction(rename_action)
        menu.addAction(listen_action)
        menu.addAction(add_description)
        menu.addAction(delete_action)


        # Установка меню для кнопки
        self.menu_button.setMenu(menu)

        self.header_text = QLabel(self.file_item.header.replace('\n', ' ').replace("_", " "))
        self.header_text.setFont(QFont("Arial", 12))
        self.header_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.header_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.header_text.setWordWrap(True)
        self.header_text.setObjectName("header")
        self.header_text.setStyleSheet(list_widget_header_style())

        self.file_item_text_area = ScrollLabel(self)
        self.file_item_text_area.setText(self.file_item.text)
        self.file_item_text_area.setObjectName("text_text")
        self.file_item_text_area.setMinimumHeight(40)
        self.file_item_text_area.setMaximumHeight(70)

        self.duration_label = QLabel(f"{self.file_item.duration} сек")
        self.duration_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.duration_label.setStyleSheet(duration_label_style())
        self.duration_label.setWordWrap(False)
        self.duration_label.setFont(QFont("Arial", 10))

        self.create_date_label = QLabel(f"{self.file_item.create_date}")
        self.create_date_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.create_date_label.setStyleSheet(create_date_label_style1())
        self.create_date_label.setWordWrap(False)
        self.create_date_label.setFont(QFont("Arial", 10))

        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.header_text)
        self.header_layout.addWidget(self.menu_button)

        self.bottom_info_layout = QHBoxLayout()
        self.bottom_info_layout.setSpacing(18)
        self.bottom_info_layout.addWidget(self.duration_label)
        self.bottom_info_layout.addWidget(self.create_date_label)

        if self.file_item.current_voice is not None:
            current_voice = ""
            if self.file_item.current_voice == "fg":
                current_voice = "мужской доброжелательный"
            elif self.file_item.current_voice == "fn":
                current_voice = "мужской нейтральный"
            elif self.file_item.current_voice == "ag":
                current_voice = "женский доброжелательный"
            elif self.file_item.current_voice == "an":
                current_voice = "женский нейтральный"

            self.current_voice_label = QLabel(f"голос: {current_voice}")
            self.current_voice_label.setWordWrap(False)
            self.current_voice_label.setFont(QFont("Arial", 10))
            self.current_voice_label.setStyleSheet(voice_label_style())

            self.create_date_label.setStyleSheet(create_date_label_style2())

            self.bottom_info_layout.addWidget(self.current_voice_label)

        self.bottom_info_layout.addStretch()  # чипы компактные, прижаты влево

        self.file_item_container.setContentsMargins(14, 12, 14, 12)
        self.file_item_container.setSpacing(8)
        self.file_item_container.addLayout(self.header_layout)
        self.file_item_container.addWidget(self.file_item_text_area)
        self.file_item_container.addLayout(self.bottom_info_layout)
        self.setLayout(self.file_item_container)

        # Установите цвет рамки
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('grey'))
        self.setPalette(palette)

    def set_selected(self, on: bool):
        """Подсветка карточки выбранного файла акцентной рамкой."""
        if on:
            t = tokens_for(_get_theme())
            self.setStyleSheet(
                f"QWidget#fileCard {{ background: {t.card}; border: 2px solid {t.accent}; border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet("")

    def rename_file(self):
        self.rename_clicked.emit(self.file_item)

    def delete_file(self):
        self.delete_clicked.emit(self.file_item)

    def listen_file(self):
        self.listen_clicked.emit(self.file_item)

    def add_description(self):
        self.add_description_clicked.emit(self.file_item)
