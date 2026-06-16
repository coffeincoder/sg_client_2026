import json
import os
from threading import Timer
import schedule
import time
from datetime import datetime, timedelta
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Scheduler(QThread):
    def __init__(self, path, callback):
        super().__init__()
        self.path = path
        self.schedules = []
        self.callback = callback
        self.running = True
        self.last_run_times = {}  # Словарь для хранения времени последнего выполнения задач
        self.load_schedules()

    def load_schedules(self):
        try:
            print("Загрузка расписаний...")
            self.schedules.clear()
            schedule.clear()  # Очистка существующих задач

            for filename in os.listdir(self.path):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.path, filename)
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        schedule_data = json.load(json_file)
                        self.schedules.append((schedule_data, filename))
                        print(f"Загружено расписание из файла: {filename}")

            self.schedule_tasks()  # Запланировать задачи после загрузки

        except FileNotFoundError:
            self._create_new_schedule_dir()


    def _create_new_schedule_dir(self):
        os.mkdir(self.path)
        self.load_schedules()


    def schedule_tasks(self):
        print("Запланированные задачи очищены.")
        for schedule_data, filename in self.schedules:
            times = schedule_data.get("times", [])
            selected_days = schedule_data.get("selected_days", [])
            for time_str, days in zip(times, selected_days):
                for day in days:
                    self.schedule_task(time_str, day, filename, schedule_data.get("scenario_name"))
        print("Запланированные задачи:")
        for job in schedule.get_jobs():
            print(job)

    def schedule_task(self, time_str, day, filename, scenario_name):
        day_map = {
            "Пн": "monday",
            "Вт": "tuesday",
            "Ср": "wednesday",
            "Чт": "thursday",
            "Пт": "friday",
            "Сб": "saturday",
            "Вс": "sunday"
        }
        job = getattr(schedule.every(), day_map[day]).at(time_str).do(self.run_task, filename, scenario_name)
        print(f"Запланирована задача '{scenario_name}' на {day} в {time_str} из файла '{filename}'")

    def run_task(self, filename, scenario_name):
        task_id = (filename, scenario_name)  # Уникальный идентификатор задачи
        current_time = datetime.now()

        # Проверка, прошло ли 5 секунд с момента последнего выполнения
        last_run_time = self.last_run_times.get(task_id)
        if last_run_time and (current_time - last_run_time) < timedelta(seconds=5):
            print(f"Задача '{scenario_name}' из файла '{filename}' была выполнена менее 5 секунд назад. Пропуск.")
            return  # Пропустить выполнение, если задача была выполнена менее 5 секунд назад

        try:
            print(f"Выполняется задача '{scenario_name}' из файла '{filename}'")
            self.callback(scenario_name, filename)
            self.last_run_times[task_id] = current_time  # Обновить время последнего выполнения задачи
            print(f"Задача '{scenario_name}' выполнена.")
        except Exception as e:
            print(f"Ошибка при выполнении задачи '{scenario_name}' из файла '{filename}': {e}")

    def run(self):
        self.running = True
        self.schedule_tasks()
        print("Планировщик запущен.")
        while self.running:
            schedule.run_pending()
            print("Ожидание выполнения задач...")
            print(f"Текущее время: {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(1)

    def stop(self):
        self.running = False
        print("Планировщик остановлен.")

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, sheduler):
        self.sheduler = sheduler
        self.needs_restart = False
        self.restart_timer = None
        self.restart_delay = 1  # Задержка в 1 секунду

    def on_modified(self, event):
        if event.src_path.endswith(".json"):
            print(f"Изменен файл: {event.src_path}. Отметка для перезапуска планировщика.")
            if not self.needs_restart:
                self.needs_restart = True
                self.start_restart_timer()

    def start_restart_timer(self):
        if self.restart_timer is not None:
            self.restart_timer.cancel()  # Отменить предыдущий таймер, если он существует
        self.restart_timer = Timer(self.restart_delay, self.check_and_restart_scheduler)
        self.restart_timer.start()

    def check_and_restart_scheduler(self):
        if self.needs_restart:
            print("Перезапуск планировщика.")
            self.sheduler.stop()  # Остановить текущий планировщик
            self.sheduler.wait()  # Подождать завершения потока

            try:
                self.sheduler.load_schedules()  # Перезагрузить расписания
                print("Расписания загружены.")
            except Exception as e:
                print(f"Ошибка при загрузке расписаний: {e}")

            if not self.sheduler.isRunning():  # Проверка, что поток не запущен
                print("Запуск нового планировщика.")
                self.sheduler.start()  # Запустить новый планировщик
            else:
                print("Планировщик уже запущен.")
            self.needs_restart = False
