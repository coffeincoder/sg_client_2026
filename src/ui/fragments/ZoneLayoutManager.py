# src/ui/ZoneLayoutManager.py
from datetime import datetime
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QPushButton, QListWidget, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
    QComboBox, QListWidgetItem, QListView, QGroupBox, QDialog, QDialogButtonBox,
    QMessageBox, QCheckBox, QScrollArea, QSizePolicy
)
import json
import paths
from src.data.ScenarioItemModel import ScenarioItemModel
from src.data.ScenarioModel import ScenarioModel
from src.ui.fragments.SheduleWindow import ScheduleWindow


class ZoneLayoutManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.is_layout_created = False
        self.clear_layout(self.main_window.scenarios_layout)

    def sizeHint(self, option, index):
        fm = QFontMetrics(index.data(Qt.FontRole) or option.font)
        text = index.data(Qt.DisplayRole)
        size = fm.boundingRect(option.rect, Qt.TextWordWrap, text).size()
        size.setWidth(option.rect.width())
        return QSize(size.width(), size.height() + 10)

    def paint(self, painter, option, index):
        fm = QFontMetrics(index.data(Qt.FontRole) or option.font)
        text = index.data(Qt.DisplayRole)
        painter.drawText(option.rect, Qt.TextWordWrap, text)

    def setup_combobox_style(self, combobox):
        """Применяет стиль и настраивает QListView для переноса текста."""
        combobox.setStyleSheet("""
            QComboBox {
                color: #D8DEE9;
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 3px;
                padding: 3px;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                color: #D8DEE9;
                background-color: #3B4252;
                selection-background-color: #4C566A;
                border: 1px solid #4C566A;
            }
        """)
        list_view = QListView()
        list_view.setWordWrap(True)
        list_view.setStyleSheet("""
            QListView {
                color: #D8DEE9;
                background-color: #3B4252;
                border: 1px solid #4C566A;
                show-decoration-selected: 1;
            }
            QListView::item {
                padding: 5px;
            }
            QListView::item:selected {
                background-color: #4C566A;
            }
        """)
        combobox.setView(list_view)

    def scen_save(self):
        scenario_items = []
        for layout in self.main_window.scen_layouts:
            zone_label = layout.itemAt(0).widget().text()
            combox_main = layout.itemAt(1).widget()
            combox_esp = layout.itemAt(2).widget()

            selected_file = combox_main.currentText()
            selected_file_esp = combox_esp.currentText() or ""

            scenario_item = ScenarioItemModel(
                zone=zone_label,
                file=selected_file,
                file_esp=selected_file_esp
            )
            scenario_items.append(scenario_item)

        scenario_name = self.main_window.scenario_title_edit.text().strip()
        if not scenario_name:
            #QMessageBox.warning(self.main_window, "Ошибка", "Введите название сценария.")
            return

        scenario = ScenarioModel(scenarioName=scenario_name, ScenarioItems=scenario_items)
        self.save_scen(scenario)

    def scen_load(self):
        self.scen_save()  # Сохраняем текущее состояние перед загрузкой
        selected_item = self.main_window.scenario_listwidget.currentItem()
        scenario_name = selected_item.text() if selected_item else None

        scenario = self.load_scen(scenario_name)
        if not scenario:
            return

        for layout in self.main_window.scen_layouts:
            zone_label = layout.itemAt(0).widget().text()
            combox_main = layout.itemAt(1).widget()
            combox_esp = layout.itemAt(2).widget()

            saved_item = next((item for item in scenario.ScenarioItems if item.zone == zone_label), None)
            if saved_item:
                combox_main.setCurrentText(saved_item.file)
                combox_esp.setCurrentText(saved_item.file_esp)

        self.main_window.scenario_title_edit.setText(scenario.scenarioName)

    def save_scen(self, scenario: ScenarioModel):
        """
        Сохраняет сценарий в JSON-файл, включая filename_esp в file_data,
        если для зоны выбран ESP-файл.
        """
        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)
        except FileNotFoundError:
            all_scenarios = {}

        scenario_dict = {
            "scenarioName": scenario.scenarioName,
            "ScenarioItems": []
        }

        for item in scenario.ScenarioItems:
            # Ищем данные зоны
            zone_data = next(
                (zone for zone in self.main_window.zones_repo.get_all() if zone.name == item.zone),
                None
            )

            # Ищем данные основного файла
            file_data = next(
                (file for file in self.main_window.files_repo.file_list if file.header == item.file),
                None
            )

            # Ищем ESP-файл и получаем его filename
            filename_esp = None
            if item.file_esp:  # Если выбран ESP-файл
                esp_file = next(
                    (file for file in self.main_window.files_repo.file_list if file.header == item.file_esp),
                    None
                )
                if esp_file:
                    filename_esp = esp_file.filename  # Сохраняем только filename

            # Преобразуем file_data в словарь и добавляем filename_esp
            file_data_dict = file_data.to_json() if file_data else None
            if file_data_dict is not None:
                file_data_dict["filename_esp"] = filename_esp  # Добавляем новое поле

            # Формируем итоговый словарь для текущего элемента сценария
            scenario_item_dict = {
                "zone": item.zone,
                "file": item.file,
                "file_esp": item.file_esp,
                "zone_data": zone_data.to_json() if zone_data else None,
                "file_data": file_data_dict  # Уже с filename_esp
            }

            scenario_dict["ScenarioItems"].append(scenario_item_dict)

        # Обновляем сценарий в общем списке
        all_scenarios[scenario.scenarioName] = scenario_dict

        # Записываем обратно в файл
        with open(paths.scenario, 'w', encoding='utf-8') as f:
            json.dump(all_scenarios, f, ensure_ascii=False, indent=4)

    def load_scen(self, scenario_name):
        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)

            if scenario_name in all_scenarios:
                scenario_dict = all_scenarios[scenario_name]
                return ScenarioModel.from_json(json.dumps(scenario_dict))
            else:
                print(f"Сценарий '{scenario_name}' не найден.")
                return None
        except FileNotFoundError:
            print("Файл scenarios.json не найден.")
            return None

    def create_layouts(self):
        self.clear_layout(self.main_window.scenarios_layout)
        self.is_layout_created = False

        if self.is_layout_created:
            return

        self.main_window.scen_layouts = []

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Список сценариев и кнопки ---
        list_buttons_layout = QHBoxLayout()
        list_buttons_layout.setSpacing(8)
        list_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.main_window.scenario_listwidget = QListWidget()
        self.main_window.scenario_listwidget.setFont(QFont("Arial", 11))  # Увеличен шрифт
        self.main_window.scenario_listwidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_window.scenario_listwidget.setStyleSheet("""
            QListWidget {
                color: #ECEFF4;
                border: 1px solid #4C566A;
                border-radius: 5px;
                padding: 4px;
                background-color: #2E3440;
                alternate-background-color: #3B4252;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px 0;
                border-bottom: 1px solid #434C5E;
                border-radius: 4px;
                background-color: #3B4252;
            }
            QListWidget::item:selected {
                color: #ECEFF4;
                background-color: #4C566A;
            }
            QListWidget::item:hover {
                background-color: #434C5E;
            }
        """)
        self.main_window.scenario_listwidget.itemSelectionChanged.connect(self.scen_load)

        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ('Добавить', self.add_scenario, "#5E81AC"),
            ('Удалить', self.delete_scenario, "#5E81AC"),
            ('Переименовать', self.rename_scenario, "#5E81AC"),
            ('Сохранить', self.scen_save, "#5E81AC")
        ]

        for text, callback, color in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 11))
            btn.setMinimumHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #ECEFF4;
                    border: 1px solid #4C566A;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: normal;
                }}
                QPushButton:hover {{
                    background-color: #81A1C1;
                    color: #ECEFF4;
                }}
                QPushButton:pressed {{
                    background-color: #4C566A;
                }}
                QPushButton:disabled {{
                    background-color: #4C566A;
                    color: #AEB5C0;
                    border-color: #3B4252;
                }}
            """)
            btn.clicked.connect(callback)
            buttons_layout.addWidget(btn)

        buttons_layout.addStretch()

        list_buttons_layout.addWidget(self.main_window.scenario_listwidget, 3)
        list_buttons_layout.addLayout(buttons_layout, 1)

        # --- Поле названия сценария ---
        self.main_window.scenario_title_edit = QLineEdit()
        self.main_window.scenario_title_edit.setFont(QFont("Arial", 13))  # Увеличен
        self.main_window.scenario_title_edit.setPlaceholderText("Название сценария")
        self.main_window.scenario_title_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_window.scenario_title_edit.setStyleSheet("""
            QLineEdit {
                color: #ECEFF4;
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 6px;
                padding: 8px;
                font-size: 13pt;
            }
            QLineEdit:focus {
                border: 1px solid #81A1C1;
            }
        """)

        # --- Группа зон и каналов с прокруткой ---
        group = QGroupBox("Зоны и аудиоканалы")
        group.setStyleSheet("""
            QGroupBox {
                color: #ECEFF4;
                border: 1px solid #4C566A;
                border-radius: 6px;
                margin-top: 8px;
                padding: 12px 6px 10px 6px;
                background-color: #2E3440;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                font-weight: bold;
                font-size: 12pt;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(group)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #3B4252;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4C566A;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5E81AC;
            }
        """)

        group_layout = QVBoxLayout()
        group_layout.setSpacing(8)
        group_layout.setContentsMargins(6, 6, 6, 6)
        group.setLayout(group_layout)

        # --- Заголовки ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        lbl_zone = QLabel("Зона")
        lbl_zone.setFont(QFont("Arial", 11))
        lbl_zone.setStyleSheet("font-weight: bold; color: #ECEFF4;")
        lbl_zone.setFixedWidth(130)

        lbl_chan1 = QLabel("Первый канал")
        lbl_chan1.setFont(QFont("Arial", 11))
        lbl_chan1.setStyleSheet("font-weight: bold; color: #ECEFF4;")

        lbl_chan2 = QLabel("Второй канал")
        lbl_chan2.setFont(QFont("Arial", 11))
        lbl_chan2.setStyleSheet("font-weight: bold; color: #ECEFF4;")

        header_layout.addWidget(lbl_zone)
        header_layout.addWidget(lbl_chan1, 1)
        header_layout.addWidget(lbl_chan2, 1)
        group_layout.addLayout(header_layout)

        # --- Добавление зон ---
        all_zones = self.main_window.zones_repo.get_all()
        headers = [item.header for item in self.main_window.files_repo.file_list]

        for zone in all_zones:
            zone_name = zone.name
            horizontal_layout = QHBoxLayout()
            horizontal_layout.setSpacing(8)
            horizontal_layout.setContentsMargins(0, 0, 0, 0)

            zone_label = QLabel(zone_name)
            zone_label.setFont(QFont("Arial", 11))
            zone_label.setFixedWidth(130)
            zone_label.setStyleSheet("""
                QLabel {
                    color: #D8DEE9;
                    padding: 8px 5px;
                }
            """)

            combox_chan1 = QComboBox()
            combox_chan1.setFont(QFont("Arial", 11))
            combox_chan1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.setup_combobox_style(combox_chan1)
            combox_chan1.addItems(headers)
            combox_chan1.setToolTip("Аудиофайл для первого канала")

            combox_chan2 = QComboBox()
            combox_chan2.setFont(QFont("Arial", 11))
            combox_chan2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.setup_combobox_style(combox_chan2)
            combox_chan2.addItems([""] + headers)
            combox_chan2.setToolTip("Аудиофайл для второго канала (необязательно)")

            horizontal_layout.addWidget(zone_label)
            horizontal_layout.addWidget(combox_chan1, 1)
            horizontal_layout.addWidget(combox_chan2, 1)
            combox_chan1.setFixedWidth(320)
            combox_chan2.setFixedWidth(320)
            group_layout.addLayout(horizontal_layout)
            self.main_window.scen_layouts.append(horizontal_layout)

        group_layout.addStretch()

        # --- Расписание ---
        schedule_layout = QHBoxLayout()
        schedule_layout.setSpacing(10)
        schedule_layout.setContentsMargins(0, 0, 0, 0)

        schedule_checkbox = QCheckBox("По расписанию")
        schedule_checkbox.setFont(QFont("Arial", 11))
        schedule_checkbox.setStyleSheet("""
            QCheckBox {
                color: #D8DEE9;
                spacing: 8px;
                padding: 4px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #4C566A;
                border-radius: 4px;
                background: #3B4252;
            }
            QCheckBox::indicator:checked {
                background: #81A1C1;
                border: 1px solid #5E81AC;
            }
        """)

        schedule_button = QPushButton("Задать")
        schedule_button.setFont(QFont("Arial", 11))
        schedule_button.setVisible(False)
        schedule_button.setStyleSheet("""
            QPushButton {
                background-color: #81A1C1;
                color: #ECEFF4;
                border: 1px solid #4C566A;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
        """)
        schedule_button.clicked.connect(self.schedule_button_clicked)

        schedule_checkbox.stateChanged.connect(
            lambda state: schedule_button.setVisible(state == Qt.Checked)
        )

        schedule_layout.addWidget(schedule_checkbox)
        schedule_layout.addWidget(schedule_button)
        schedule_layout.addStretch()

        # --- Сборка всего ---
        layout.addLayout(list_buttons_layout, 1)
        layout.addWidget(self.main_window.scenario_title_edit, 0)
        layout.addWidget(scroll, 3)
        layout.addLayout(schedule_layout, 0)

        self.main_window.scenarios_layout.addLayout(layout)
        self.is_layout_created = True
        self.update_listwidget()
    def schedule_button_clicked(self):
        selected_item = self.main_window.scenario_listwidget.currentItem()
        if selected_item:
            scenario_name = selected_item.text()
            self.schedule_window = ScheduleWindow(self.main_window, scenario_name)
            self.schedule_window.showMaximized()

    def update_listwidget(self):
        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)
            scenario_names = list(all_scenarios.keys())
        except FileNotFoundError:
            scenario_names = []

        self.main_window.scenario_listwidget.clear()
        for name in scenario_names:
            if name.strip():
                item = QListWidgetItem(name)
                self.main_window.scenario_listwidget.addItem(item)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def add_scenario(self):
        now = datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        scenario_name = 'Новый сценарий от ' + formatted_datetime
        scenario = ScenarioModel(scenarioName=scenario_name, ScenarioItems=[])
        self.save_scen(scenario)
        self.main_window.scenario_title_edit.setText(scenario_name)
        self.update_listwidget()

    def delete_scenario(self):
        scenario_name = self.main_window.scenario_title_edit.text().strip()
        if not scenario_name:
            return

        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)
            if scenario_name in all_scenarios:
                del all_scenarios[scenario_name]
                with open(paths.scenario, 'w', encoding='utf-8') as f:
                    json.dump(all_scenarios, f, ensure_ascii=False, indent=4)
            self.main_window.scenario_title_edit.clear()
            self.update_listwidget()
        except FileNotFoundError:
            pass

    def rename_scenario(self):
        current_name = self.main_window.scenario_title_edit.text().strip()
        if not current_name:
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle('Переименовать сценарий')
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2E3440;
            }
            QLabel {
                color: #D8DEE9;
            }
        """)

        layout = QVBoxLayout()
        line_edit = QLineEdit(current_name)
        line_edit.setStyleSheet("""
            QLineEdit {
                color: #D8DEE9;
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 3px;
                padding: 5px;
            }
        """)

        layout.addWidget(QLabel("Новое название:"))
        layout.addWidget(line_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: 1px solid #4C566A;
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #434C5E;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_name = line_edit.text().strip()
            if not new_name:
                QMessageBox.warning(dialog, "Ошибка", "Имя не может быть пустым.")
                return

            try:
                with open(paths.scenario, 'r', encoding='utf-8') as f:
                    all_scenarios = json.load(f)
                if current_name in all_scenarios:
                    all_scenarios[new_name] = all_scenarios.pop(current_name)
                    with open(paths.scenario, 'w', encoding='utf-8') as f:
                        json.dump(all_scenarios, f, ensure_ascii=False, indent=4)
                self.main_window.scenario_title_edit.setText(new_name)
                self.update_listwidget()
            except FileNotFoundError:
                pass