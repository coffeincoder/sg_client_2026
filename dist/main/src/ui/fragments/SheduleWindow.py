import json
import os

from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QFrame,
    QScrollArea,
    QTimeEdit,
    QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTime

import paths
from src.operation_with_scenaries.Sheduler import Sheduler


class ScheduleWindow(QMainWindow):
    def __init__(self, parent, scenario_name):
        super().__init__(parent)
        self.setWindowTitle(f"Задать расписание для сценария '{scenario_name}'")
        self.setFixedSize(850, 600)  # Устанавливаем фиксированный размер окна
        self.scenario_name = scenario_name

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        self.main_layout = QVBoxLayout(central_widget)

        # Заголовок
        title_label = QLabel(f"Задать расписание для сценария '{scenario_name}'")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px;")
        self.main_layout.addWidget(title_label)

        # Создаем QScrollArea для прокручиваемого контента
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(500)  # Устанавливаем фиксированную высоту для области прокрутки
        self.main_layout.addWidget(self.scroll_area)

        # Создаем виджет для содержимого прокручиваемой области
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        self.content_layout = QVBoxLayout(self.content_widget)  # Новый layout для динамических элементов
        self.content_layout.setSpacing(30)  # Увеличиваем отступ между элементами
        self.content_layout.setContentsMargins(15, 15, 15, 15)

        self.time_input_fields = []

        # Добавляем заголовок для времени
        self.time_label = QLabel("Время:")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        self.content_layout.addWidget(self.time_label)

        # Попробуем загрузить расписание при инициализации
        self.load_schedule()  # Загружаем расписание автоматически

        # Создаем layout для кнопок
        self.create_button_layout()

    def create_button_layout(self):
        """Создает layout для кнопок управления."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(15, 15, 15, 15)

        # Кнопка добавления времени
        add_button = QPushButton('Добавить время')
        add_button.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 5px;")
        add_button.clicked.connect(self.add_time_input_field)
        buttons_layout.addWidget(add_button)

        # Кнопка сохранения
        save_button = QPushButton('Сохранить')
        save_button.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #2196F3; color: white; border: none; border-radius: 5px;")
        save_button.clicked.connect(self.save_schedule)  # Метод для обработки сохранения
        buttons_layout.addWidget(save_button)

        # Добавляем кнопки в основной макет
        self.main_layout.addLayout(buttons_layout)

        # Добавляем отступ после кнопок
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)

    def create_time_input_field(self, num, selected_days=None):
        """Создает поле ввода времени и соответствующие чекбоксы для дней недели."""
        time_input_field = QTimeEdit()
        time_input_field.setDisplayFormat('HH:mm')  # Устанавливаем формат отображения
        time_input_field.setFixedWidth(100)  # Установите ширину для QTimeEdit
        time_input_field.setFixedHeight(60)  # Установите фиксированную высоту для поля ввода
        time_input_field.setStyleSheet("font-size: 24px;")  # Увеличиваем размер шрифта

        # Создаем чекбоксы для дней недели
        day_checkboxes = {}
        days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        days_layout = QHBoxLayout()  # Горизонтальный layout для чекбоксов

        for day in days_of_week:
            checkbox = QCheckBox(day)
            checkbox.setStyleSheet("font-size: 16px;")  # Увеличиваем размер чекбоксов
            days_layout.addWidget(checkbox)
            day_checkboxes[day] = checkbox

        # Устанавливаем состояние чекбоксов в соответствии с загруженными данными, если они есть
        if selected_days:
            for day in days_of_week:
                if day in selected_days:
                    day_checkboxes[day].setChecked(True)

        # Создаем фрейм для всех элементов input
        frame = QFrame()
        frame.setFixedHeight(80)  # Установите фиксированную высоту для фрейма
        frame.setFrameShape(QFrame.NoFrame)  # Убедитесь, что фрейм не имеет границы
        frame.setLayout(QHBoxLayout())  # Создаем layout для фрейма

        # Создаем метку для времени
        time_label = QLabel(f'Время {num}:')
        time_label.setStyleSheet("font-size: 28px; font-weight: bold;")  # Увеличиваем размер шрифта
        frame.layout().addWidget(time_label)

        frame.layout().addWidget(time_input_field)

        # Создаем фрейм для чекбоксов
        day_frame = QFrame()
        day_frame.setFrameShape(QFrame.Box)
        day_frame.setFrameShadow(QFrame.Raised)
        day_frame.setLayout(days_layout)

        # Добавляем фрейм с чекбоксами
        frame.layout().addWidget(day_frame)

        # Создаем кнопку удаления
        delete_button = QPushButton('Удалить')
        delete_button.setStyleSheet(
            "font-size: 14px; padding: 5px; background-color: #f44336; color: white; border: none; border-radius: 5px;")
        delete_button.clicked.connect(lambda: self.remove_time_input_field(frame))  # Удаляем поле
        frame.layout().addWidget(delete_button)

        # Добавляем временное поле в прокручиваемый layout
        self.content_layout.addWidget(frame)  # Используется QFrame, который имеет фиксированную высоту
        self.time_input_fields.append((time_input_field, day_checkboxes, frame))  # Сохраняем фрейм для удаления

        # Добавляем отступ после каждого элемента
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.content_layout.addItem(spacer)

    def add_time_input_field(self):
        """Добавляет новое поле ввода времени в интерфейсе."""
        num = len(self.time_input_fields) + 1
        self.create_time_input_field(num)

    def remove_time_input_field(self, frame):
        """Удаляет поле ввода времени и соответствующие элементы."""
        # Удаляем фрейм из layout
        self.content_layout.removeWidget(frame)
        frame.deleteLater()  # Удаляем фрейм
        # Удаляем из списка полей ввода
        self.time_input_fields = [item for item in self.time_input_fields if item[2] != frame]

    def get_selected_days(self):
        """Возвращает список всех выбранных дней."""
        selected_days = []
        for _, day_checkboxes, _ in self.time_input_fields:
            days = []
            for day, checkbox in day_checkboxes.items():
                if checkbox.isChecked():
                    days.append(day)
            selected_days.append(days)
        return selected_days

    def get_times(self):
        """Возвращает список всех введенных времен."""
        return [field.time().toString('HH:mm') for field, _, _ in self.time_input_fields]  # Изменено на использование QTime

    def save_schedule(self):
        """Метод для обработки сохранения расписания."""
        times = self.get_times()
        selected_days = self.get_selected_days()

        # Создаем словарь для сохранения данных
        schedule_data = {
            "scenario_name": self.scenario_name,
            "times": times,
            "selected_days": selected_days
        }

        # Формируем имя файла на основе названия сценария
        file_name = os.path.join(paths.shedule_data_scenaries, f"{self.scenario_name}.json").replace(":", '-')

        # Сохраняем данные в файл
        with open(file_name, 'w', encoding='utf-8') as json_file:
            json.dump(schedule_data, json_file, ensure_ascii=False, indent=4)
        print("Расписание сохранено:", schedule_data)

    def load_schedule(self):
        """Метод для обработки загрузки расписания."""
        # Формируем имя файла на основе названия сценария
        file_name = os.path.join(paths.shedule_data_scenaries, f"{self.scenario_name}.json").replace(':', '-')

        try:
            with open(file_name, 'r', encoding='utf-8') as json_file:
                schedule_data = json.load(json_file)

            # Обновляем заголовок окна
            self.scenario_name = schedule_data.get("scenario_name", self.scenario_name)
            self.setWindowTitle(f"Задать расписание для сценария '{self.scenario_name}'")

            # Очищаем текущие поля ввода
            self.clear_time_input_fields()

            # Заполняем новые поля ввода
            for time_str, days in zip(schedule_data.get("times", []), schedule_data.get("selected_days", [])):
                self.create_time_input_field(len(self.time_input_fields) + 1, days)  # Передаем выбранные дни
                time = QTime.fromString(time_str, 'HH:mm')  # Преобразуем строку в QTime
                self.time_input_fields[-1][0].setTime(time)  # Устанавливаем время

            print("Расписание загружено:", schedule_data)
        except FileNotFoundError:
            print(f"Файл '{file_name}' не найден. Загружено пустое расписание.")

    def clear_time_input_fields(self):
        """Очищает все поля ввода времени."""
        for field, _, frame in self.time_input_fields:
            frame.deleteLater()  # Удаляем фрейм
        self.time_input_fields.clear()
