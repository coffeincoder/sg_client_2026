from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QToolButton, QAction, QMenu)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

from paths import sep
from src.data.FileModel import FileItem
from src.ui.custom.ElidingLabel import ElidingLabel
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
        self.setObjectName("fileCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(file_list_item_style())
        self.menu_button = self._build_gear_button()
        self.header_text = self._build_header_label()
        self._build_meta_labels()
        self._assemble_layouts()
        self.setToolTip(self.file_item.text)

    def _build_gear_button(self) -> QToolButton:
        btn = QToolButton(self)
        btn.setStyleSheet("""
        QToolButton {
            border: 1px solid transparent;
            border-radius: 8px;
            background-color: transparent;
        }
        QToolButton:hover {
            border: 1px solid #2979FE;
            background-color: transparent;
        }
        QToolButton:pressed, QToolButton:open {
            border: 1px solid transparent;
            background-color: transparent;
        }
        """)
        btn.setIcon(QIcon(f"{paths.img_files}{sep}ic-gear.png"))
        btn.setIconSize(QSize(26, 26))
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setAutoRaise(True)
        btn.setFixedSize(40, 40)

        rename_action = QAction('Переименовать', self)
        delete_action = QAction('Удалить', self)
        listen_action = QAction('Прослушать', self)
        add_description_action = QAction('Редактировать описание', self)

        rename_action.triggered.connect(self.rename_file)
        listen_action.triggered.connect(self.listen_file)
        delete_action.triggered.connect(self.delete_file)
        add_description_action.triggered.connect(self.add_description)

        menu = QMenu(self)
        menu.addAction(rename_action)
        menu.addAction(listen_action)
        menu.addAction(add_description_action)
        menu.addAction(delete_action)
        btn.setMenu(menu)
        return btn

    def _build_header_label(self) -> QLabel:
        # ElidingLabel: длинное имя обрезается многоточием (…), полное — в подсказке.
        # wordWrap не годился — не разбивает длинные слова без пробелов.
        label = ElidingLabel(self.file_item.header.replace('\n', ' ').replace("_", " "))
        label.setFont(QFont("Arial", 12))
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setObjectName("header")
        label.setStyleSheet(list_widget_header_style())
        return label

    def _build_meta_labels(self) -> None:
        self.duration_label = QLabel(f"{self.file_item.duration} сек")
        self.duration_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.duration_label.setStyleSheet(duration_label_style())
        self.duration_label.setWordWrap(False)
        self.duration_label.setFont(QFont("Arial", 10))

        self.create_date_label = QLabel(f"{self.file_item.create_date}")
        self.create_date_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.create_date_label.setWordWrap(False)
        self.create_date_label.setFont(QFont("Arial", 10))

        if self.file_item.current_voice is not None:
            voice_map = {
                "fg": "мужской доброжелательный",
                "fn": "мужской нейтральный",
                "ag": "женский доброжелательный",
                "an": "женский нейтральный",
            }
            current_voice = voice_map.get(self.file_item.current_voice, "")
            self.current_voice_label = QLabel(f"голос: {current_voice}")
            self.current_voice_label.setWordWrap(False)
            self.current_voice_label.setFont(QFont("Arial", 10))
            self.current_voice_label.setStyleSheet(voice_label_style())
            self.create_date_label.setStyleSheet(create_date_label_style2())
        else:
            self.create_date_label.setStyleSheet(create_date_label_style1())

    def _assemble_layouts(self) -> None:
        # Длительность + дата — компактным столбиком справа.
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(1)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.addWidget(self.duration_label, 0, Qt.AlignRight)
        meta_layout.addWidget(self.create_date_label, 0, Qt.AlignRight)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.menu_button, 0, Qt.AlignRight | Qt.AlignTop)
        right_layout.addLayout(meta_layout)
        right_layout.addStretch()

        # Верхняя строка: заголовок слева (тянется), справа — шестерёнка/длительность/дата.
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.addWidget(self.header_text, 1, Qt.AlignVCenter)
        top_row.addLayout(right_layout)

        # Плашка голоса — отдельной строкой снизу во всю ширину, чтобы не отъедать
        # ширину у заголовка (иначе длинный «голос: …» ужимал имя файла).
        self.file_item_container = QVBoxLayout()
        self.file_item_container.setContentsMargins(12, 8, 8, 8)
        self.file_item_container.setSpacing(4)
        self.file_item_container.addLayout(top_row)
        if self.file_item.current_voice is not None:
            self.file_item_container.addWidget(self.current_voice_label)
        self.setLayout(self.file_item_container)

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
