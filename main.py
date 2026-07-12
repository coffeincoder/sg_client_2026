# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import logging
import os.path
import platform
import random
import shlex
import shutil
import subprocess
import sys
import traceback
from  datetime import  datetime
import time as _time  # Изменяем импорт
import socket
from datetime import time
from time import sleep
from threading import Thread
import numpy as np
import psutil
import pyaudio
import qdarkstyle
import requests
from PyQt5.QtCore import QTimer, pyqtSlot, Qt, QEvent, QTime, QSharedMemory, QMutex
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QAction, QMessageBox, QDialog, QMenu, QFileDialog, QApplication, QTextEdit, QPushButton, \
    QComboBox, QHBoxLayout, QLabel, QTabWidget, QDesktopWidget
from qtpy import QtWidgets
from rtp import RTP, PayloadType
from watchdog.observers import Observer

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass  # exec-контекст (напр. PyCharm console) — CWD уже должен быть корнем проекта

import paths

from paths import *
from src.data.LockManager import LockManager
from src.data.ScenarioItem import ScenarioItem
from src.data.ScenarioModel import ScenarioModel
from src.data.SingleInstance import SingleInstance
from src.network.ConnectionThread import ConnectionThread
from src.data.OrangeStatus import OrangeStatus
from src.network.StatusSender import StatusSender
from src.network.UploadStaticFiles import UploadStaticFiles
from src.operation_with_scenaries.Scheduler import Scheduler, FileChangeHandler
from src.ui.custom.WaveFormViewer import VolumeVisualiser
from src.ui.fragments.ZoneLayoutManager import ZoneLayoutManager
from src.utils.LogManager import LogManager
from src.utils.SystemChecker import SystemChecker
from src.operations_with_files.AudioRecorder import Recorder
from src.network.AudioStremer import AudioStreamer
from src.operations_with_zones.ZoneItemRepository import ZoneItemRepository
from src.ui.fragments.AddDescriptionDialog import AddDescriptionDialog
from src.ui.fragments.LoadingScreen import LoadingScreen
from src.utils.OrangeStatusAPI import StatusAPI
from src.utils.Yandex import YandexThread
from src.utils.FfmpegWork import FfmpegThread
from src.network.OrangeWorkerTCP import OrangeWorkerTCP
from src.utils.Recognizer import Recognizer
from src.ui.fragments.RenameDialog import Rename_Dialog
from src.operations_with_files.FileItemRepository import *
from src.ui.fragments.SettingsDialog import SettingsDialog
from src.ui.style_sheets import *
from src.ui.fragments.UI_AddZoneWindow import UI_AddZoneWindow
from src.ui.root.UI_MainWindow import Ui_MainWindow
from src.data.ZoneModel import Orange
from src.utils.logger_config import setup_logger


import os
import sys
import psutil

# Настройка логгера для отладки блокировки
lock_logger = logging.getLogger('lock_manager')
lock_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
lock_logger.addHandler(handler)


def check_lock(lock_file: str) -> bool:
    """Проверить возможность запуска приложения"""
    try:
        if not os.path.exists(lock_file):
            lock_logger.info("Файл блокировки отсутствует, разрешаем запуск")
            return True

        with open(lock_file, 'r') as f:
            content = f.read().strip()

        if not content:
            lock_logger.info("Файл блокировки пуст, разрешаем запуск")
            return True

        last_time = float(content)
        current_time = _time.time()

        lock_logger.info(
            f"Текущее время: {current_time}, время блокировки: {last_time}, разница: {current_time - last_time}")

        # Проверяем свежесть метки (30 секунд - максимальный возраст)
        if (current_time - last_time) > 30:
            lock_logger.info("Метка устарела, разрешаем запуск")
            return True
        else:
            lock_logger.info("Свежая метка блокировки, запрещаем запуск")
            return False
    except Exception as e:
        lock_logger.error(f"Ошибка проверки блокировки: {e}")
        return True


def remove_lock_file(lock_file):
    # Удаляем файл блокировки при завершении приложения
    if os.path.exists(lock_file):
        os.remove(lock_file)

def driver_reload():
    processes = psutil.process_iter()
    for process in processes:
        try:
            # Получаем список открытых файлов процесса
            open_files = process.open_files()
            for file in open_files:
                if '/dev/snd/' in file.path:
                    logger.info(f"\ndriver_reload: Найден процесс с PID {process.pid}, завершение...\n")
                    process.terminate()
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            pass


def set_light_theme():
    with open(paths.settings, 'r') as s:
        settings_dict = json.load(s)
    settings_dict["theme"] = "light"
    with open(paths.settings, 'w') as s:
        json.dump(settings_dict, s)


def set_dark_theme():
    with open(paths.settings, 'r') as s:
        settings_dict = json.load(s)
    settings_dict["theme"] = "dark"
    with open(paths.settings, 'w') as s:
        json.dump(settings_dict, s)


from src.utils.app_helpers import (
    convert_seconds, sanitize_filename, cut_filename,
    last_five_chars_of_datetime_timestamp, settings, mic_is_ready,
)


class  MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, application):
        super(MainWindow, self).__init__()
        self.start_time = None

        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setAcceptDrops(True)
        self.setupUi(self)

        try:
            _script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            _script_dir = os.getcwd()
        _vfile = os.path.join(_script_dir, "VERSION")
        if os.path.exists(_vfile):
            with open(_vfile) as _f:
                self.setWindowTitle(f"КСБ Саундгард v{_f.read().strip()}")

        self.layout_manager = ZoneLayoutManager(self)

        self.filelist_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.realtime_play_threads = []
        self.stop_realtime_threads = []
        self.play_threads = []
        self.stop_threads = []
        self.success_IPs = []
        self.finished_threads = 0

        self.app = application

        self.is_streaming_flag = False
        self.sort_key = 'create_date'
        self.name_reverse_key = True
        self.date_reverse_key = True
        self.indication = None
        self.indication_mic = None
        self.recorder = None
        self.timer_for_record = QTimer()
        self.timer_for_record.timeout.connect(self.update_record_timer)

        self.selected_voice = "мужской доброжелательный"
        self.audio_streamer = None
        addr_for_status_collector = settings()["status_collector_web_addr"]
        addr_for_status_collector = "http://192.168.252.164:9111/api.php" # - debug
        self.status_sender = StatusSender(addr_for_status_collector)

        self.play_btn.clicked.connect(self.launch_play)
        self.stop_btn.clicked.connect(self.launch_stop)
        self.text_to_file_btn.clicked.connect(self.launch_yandex_process)
        self.zone_add_btn.clicked.connect(self.add_zone)

        self.auto_search_zones_btn.clicked.connect(self.auto_search_zones)
        self.zone_refresh_btn.clicked.connect(self.launch_status_connection)

        self.repeat_check_box.clicked.connect(self.change_enabled_of_spin_box)
        self.sort_by_name_btn.clicked.connect(self.sort_by_name)
        self.sort_by_date_btn.clicked.connect(self.sort_by_date)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.upload_custom_file_btn.clicked.connect(self.upload_custom_file)

        self.record_btn.clicked.connect(self.launch_rec)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.update_volume_on_oranges_btn.clicked.connect(self.send_new_volume_value)
        self.list_scale_slider.valueChanged.connect(self.update_list_on_slider)
        self.voice_select_btn.clicked.connect(self.select_voice_menu)
        self.realtime_button.clicked.connect(self.launch_realtime)
        self.stop_realtime_button.clicked.connect(self.orange_stop_realtime)

        self.file_list_widget.delete_clicked.connect(self.delete_file)
        self.file_list_widget.listen_clicked.connect(self.play_file_local)
        self.file_list_widget.rename_clicked.connect(self.rename_file)
        self.file_list_widget.add_description_clicked.connect(self.add_description_to_file_item)

        self.zone_list_widget.rename_clicked.connect(self.rename_zone)
        self.zone_list_widget.delete_clicked.connect(self.remove_zone)

        self.waveform_viewer = VolumeVisualiser()

        self.set_volume()

        self.repeat_spin_box.setValue(5)

        self.mic_usage_indicator.setVisible(False)

        self.zones_repo = ZoneItemRepository()
        self.files_repo: FileItemRepository = FileItemRepository()

        self.FILE_LIST = self.files_repo.get()
        self.ZONE_LIST = self.zones_repo.all_zones

        self.status_api = StatusAPI(port=1883, topic="sg/statuses")
        self.status_api.status_changed.connect(self.orange_status_receiver)

        self.connection_thread = ConnectionThread(self.status_api, self.ZONE_LIST)
        self.connection_thread.connected.connect(self.on_connected)

        with open(paths.grid) as f:
            self.grid_size = int(f.read())
        self.list_scale_slider.setValue(self.grid_size)
        self.update_zones()
        self.update_list_on_slider(self.grid_size)
        self.system_checker: SystemChecker = SystemChecker(
            callback=self.update_statuses,
            check_interval=settings()["check_interval"]
        )
        self.init_menu_bar()
        self.apply_theme()
        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()

        # Устанавливаем размеры окна равными размерам экрана
        self.setGeometry(0, 0, width, height)
        self.sheduler = Scheduler(paths.shedule_data_scenaries, self.on_task_executed)
        self.sheduler.start()

        # Set up file monitoring
        self.event_handler = FileChangeHandler(self.sheduler)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, paths.shedule_data_scenaries, recursive=False)
        self.observer.start()

        print(self.file_list_widget.rowCount())
        if self.file_list_widget.rowCount() == 0:

            reply = QMessageBox.question(self, 'У вас нет ни одного  записанного файлла', 'загрузить шаблоны файлов из репозитория КСБ?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:

                # Испускание сигнала с новым значением переменной

                uploader = UploadStaticFiles()
                data_list = uploader.get_data_as_list()
                for data in data_list:
                    self.yandex_things(data)
                print(data_list)

    def on_modified(self, event):
        print(f"Событие изменения файла: {event.src_path}")
        if event.src_path.endswith(".json"):
            print(f"Изменен файл: {event.src_path}. Перезапуск планировщика.")
            self.sheduler.stop()  # Остановить текущий планировщик
            self.sheduler.wait()  # Подождать завершения потока

            self.sheduler.load_schedules()  # Перезагрузить расписания
            if not self.sheduler.isRunning():  # Проверка, что поток не запущен
                print("Запуск нового планировщика.")
                self.sheduler.start()  # Запустить новый планировщик
            else:
                print("Планировщик уже запущен.")
    import json
    def on_task_executed(self, s_name, filename):
        # Создание окна сообщения

        sleep(1)
        #scenario_name = self.layout_manager.main_window.scenario_listwidget.currentItem().text()
        print(s_name)
        print('11111111111111111111111111111111111111')
        asyncio.run(self.orange_play_scenario(scenario_name=s_name))
        print('22222222222222222222222222222222222222')
        sleep(1)
        # Отображение окна сообщения

    def closeEvent(self, event):
        if self.lock_manager:
            self.lock_manager.stop()

        self.sheduler.terminate()
        self.observer.stop()
        self.observer.join()

        self.zone_list_widget.save_zones()
        event.accept()
    def load_scenarios(self):
        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)
        except FileNotFoundError:
            return {}

        scenarios = {}

        for scenario_name, scenario_data in all_scenarios.items():
            scenario_items = []

            for item in scenario_data["ScenarioItems"]:
                # Восстанавливаем объект Orange (зону)
                zone_data = item.get("zone_data")
                zone_obj = Orange(**zone_data) if zone_data else None

                # Восстанавливаем объект FileItem (файл)
                file_data = item.get("file_data")
                file_obj = FileItem.from_json(file_data) if file_data else None

                # Создаем объект сценария (предполагается, что у вас есть соответствующий класс)
                scenario_item = ScenarioItem(
                    zone=zone_obj,
                    file=file_obj
                )

                scenario_items.append(scenario_item)

            # Создаем объект ScenarioModel (или другой соответствующий класс)
            scenario = ScenarioModel(
                scenarioName=scenario_name,
                ScenarioItems=scenario_items
            )

            scenarios[scenario_name] = scenario

        return scenarios


    def on_tab_changed(self, index):
        """Slot method called when the tab is changed."""
        index=self.filelist_tab_widget.currentIndex()
        if index==1:
            layout = self.add_file_buttons_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(False)

        if index ==0:
            layout = self.add_file_buttons_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(True)
        self.test()
        self.repaint()

    def test(self):

        self.layout_manager.create_layouts()

        # # Добавление двух элементов (например, кнопок) в горизонтальный layout
        # button1 = QPushButton("Button 1")
        # button2 = QPushButton("Button 2")
        # self.horizontal_layout.addWidget(button1)
        # self.horizontal_layout.addWidget(button2)
        #
        # # Добавление горизонтального layout в основной вертикальный layout
        # self.scenaries_tab_layout.addLayout(self.horizontal_layout)
        #
        #
        # zo=self.zones_repo.get_all()
        # print(zo)
        #
        # file_items = self.files_repo.file_list
        #
        # # Получение списка заголовков (header)
        # headers = [item.header for item in file_items]
        # for header in headers:
        #     self.btn.addItem(header)
        # # Вывод списка заголовков
        # print(headers)

    def launch_system_checker(self):
        if not self.system_checker.isRunning():
            self.system_checker.start()

    def launch_status_connection(self):
        self.zone_refresh_btn.setEnabled(False)
        self.zone_process_indicator.setVisible(True)
        self.zone_process_indicator.indicate()
        if not self.connection_thread.isRunning():
            logger.info(f"main: launch_status_connection")
            self.connection_thread.start()

    @pyqtSlot(bool, str)
    def update_online_status(self, is_online: bool, ip: str):
        for zone in self.ZONE_LIST:
            if ip == zone.ip:
                zone.is_online = is_online
        self.update_zones()

    def update_statuses(self):
        self.commit_orange_command(command="status", thread_list=self.play_threads)
        for zone in self.ZONE_LIST:
            zone.is_online = self.status_api.is_online(zone.ip)
            logger.info(f"main: on_connected {zone.name} - {zone.is_online}")
        # self.update_zones()
        if not self.status_sender.isRunning():
            self.status_sender.start()
        self.zone_refresh_btn.setEnabled(True)
        self.zone_process_indicator.setVisible(False)
        self.zone_process_indicator.stopIndicate()

    def on_connected(self):
        logger.info(f"main: on_connected")
        self.commit_orange_command(command="status", thread_list=self.play_threads)
        for zone in self.ZONE_LIST:
            logger.info(f"main: on_connected {zone.name} - {zone.is_online}")
            self.status_api.is_online(zone.ip)
        # self.update_zones()
        self.zone_refresh_btn.setEnabled(True)
        self.zone_process_indicator.setVisible(False)
        self.zone_process_indicator.stopIndicate()
        logger.info(f"main: on_connected self.connection_thread.isRunning() - {self.connection_thread.isRunning()}")

    def send_new_volume_value(self):
        self.commit_orange_command("vol", self.play_threads, vol=self.volume_slider.value())

    def launch_yandex_process(self):
        print('yandex')
        try:
            self.yandex_things()
        except Exception as e:
            logger.info(f"launch_yandex_process: {e}")

    def launch_realtime(self):
        if not self.is_streaming_flag:
            if mic_is_ready():
                self.orange_realtime()
            else:
                self.handle_no_microphone()

    def launch_play(self):
        if not self.is_streaming_flag:

            index = self.filelist_tab_widget.currentIndex()
            if index==0:
                asyncio.run(self.orange_play())
            if index==1:

                scenario_name = self.layout_manager.main_window.scenario_listwidget.currentItem().text()
                print(scenario_name)
                asyncio.run(self.orange_play_scenario(scenario_name=scenario_name))




    def launch_rec(self):
        if not self.is_streaming_flag:
            self.progress_indicator.indicate()
            if mic_is_ready():
                self.do_rec()
            else:
                self.handle_no_microphone()

    def launch_stop(self):
        """stop operations 1"""
        if not self.is_streaming_flag:
            self.progress_indicator.indicate()
            self.orange_stop()

    def commit_orange_command(
            self,




            command: str,
            thread_list: list,
            filename=None,
            ip=None,
            text=None,
            loop=None,
            vol=None,
            overload_value=0,
            is_rtp=False
    ):
        if is_rtp:
            logger.info("__RTP")
        else:
            logger.info(f"common orange command - {command}")
        zones = self.ZONE_LIST

        self.realtime_play_threads.clear()
        self.stop_realtime_threads.clear()
        self.play_threads.clear()
        self.stop_threads.clear()
        self.success_IPs.clear()

        for zone in zones:
            if zone.isChecked:
                self.progress_indicator.indicate()
                logger.info(f"commit_command({command}): зона '{zone.name}|{zone.ip}' установлена")
                print(command)

                _play_variant = None
                if zone.subzone1 and zone.subzone2:
                    _play_variant = 'channel_1_2'
                elif zone.subzone1 and not zone.subzone2:
                    _play_variant = 'channel_1'
                elif not zone.subzone1 and  zone.subzone2:
                    _play_variant = 'channel_2'
                elif not zone.subzone2 and not zone.subzone2:
                    _play_variant = 'no_channel'


                t = OrangeWorkerTCP(
                    command=command,
                    ip=str(zone.ip),
                    text=text,
                    loop=loop,
                    file_path=filename,
                    vol=vol,
                    overload_value=overload_value,
                    play_variant=_play_variant
                )

                t.signal.connect(self.indicate_file_played_on_orange)  # подключите функцию, которая обновит GUI
                t.status.connect(self.tcp_orange_callback_status)
                t.signal_progress_bar.connect(self.progress_update)
                t.success_rtp_signal.connect(self.on_orange_success)
                t.final_signal.connect(self.on_orange_finished)
                t.online_check.connect(self.update_online_status)
                thread_list.append(t)
                logger.info(
                    f"commit_command({command}): список потоков для команды ({len(thread_list)}) : {thread_list}")

        if command != 'vol':
            self.mic_usage_indicator.setVisible(False)

        for thread in thread_list:
            logger.info(f"commit_command({command}): поток {thread} запущен")
            thread.start()
            if is_rtp:
                thread.finished.connect(self.on_thread_finished)


    def commit_orange_command_scenario(
            self,
            scenario_name:str,





            command: str,
            thread_list: list,
            filename=None,
            ip=None,
            text=None,
            loop=None,
            vol=None,
            overload_value=0,
            is_rtp=False
    ):
        if is_rtp:
            logger.info("__RTP")
        else:
            logger.info(f"common orange command - {command}")
        zones = self.ZONE_LIST
        print('11111111111111111111111111')
        self.realtime_play_threads.clear()
        self.stop_realtime_threads.clear()
        self.play_threads.clear()
        self.stop_threads.clear()
        self.success_IPs.clear()
        scenarios=self.load_scenarios()
        print(scenario_name)
        specific_scenario = scenarios.get(scenario_name)
        print(specific_scenario)
        if specific_scenario:
            for item in specific_scenario.ScenarioItems:
                print(item)
                # Получаем объект Orange
                print(item.zone.ip)
                print(item.file.filename)

                #self.progress_indicator.indicate()
                #logger.info(f"commit_command({command}): зона '{zone.name}|{zone.ip}' установлена")
                t = OrangeWorkerTCP(
                    command=command,
                    ip=str(item.zone.ip),
                    text=text,
                    loop=loop,
                    file_path=os.path.join(paths.mp3_files,item.file.filename),
                    vol=vol,
                    overload_value=overload_value
                )

                t.signal.connect(self.indicate_file_played_on_orange)  # подключите функцию, которая обновит GUI
                t.status.connect(self.tcp_orange_callback_status)
                t.signal_progress_bar.connect(self.progress_update)
                t.success_rtp_signal.connect(self.on_orange_success)
                t.final_signal.connect(self.on_orange_finished)
                t.online_check.connect(self.update_online_status)
                thread_list.append(t)
                logger.info(
                    f"commit_command({command}): список потоков для команды ({len(thread_list)}) : {thread_list}")

            if command != 'vol':
                self.mic_usage_indicator.setVisible(False)

            for thread in thread_list:
                logger.info(f"commit_command({command}): поток {thread} запущен")
                thread.start()
                if is_rtp:
                    thread.finished.connect(self.on_thread_finished)

    @pyqtSlot(bool)
    def on_streaming_status_changed(self, is_streaming: bool):
        """Подключен к AudioStreamer и получает сигнал либо о старте трансляции либо об остановке"""
        self.is_streaming_flag = is_streaming
        if is_streaming:
            self.stop_realtime_button.setIcon(QIcon(paths.img_files + os.sep + "broadcast-off-red.png"))
        else:
            self.stop_realtime_button.setIcon(QIcon(paths.img_files + os.sep + "broadcast-off-custom.png"))

    def on_thread_finished(self):
        self.finished_threads += 1
        if self.finished_threads == len(self.realtime_play_threads):
            self.start_rtp_session(self.success_IPs)
            self.finished_threads = 0

    async def orange_play(self):
        # self.initList()
        self.play_threads = []
        loop = 0
        volume = 100
        overload_value = 0
        filename = self.get_file_item_file_name()

        file_path = f"{paths.mp3_files}{paths.sep}{filename}"
        if not self.repeat_check_box.isChecked():
            loop = 1
        else:
            logger.info(loop)
            loop = str(self.repeat_spin_box.value())
        if self.volume_slider.value() <= 100:
            volume = str(self.volume_slider.value())
            overload_value = 0
        else:
            volume = 100
            overload_value = int(self.volume_slider.value()) - 100
        try:
            if file_path is not None:
                self.commit_orange_command(command="play",

                                           thread_list=self.play_threads,
                                           filename=file_path,
                                           text='',
                                           loop=loop,
                                           vol=volume,
                                           overload_value=overload_value
                                           )
                # self.now_playing.change_gif(f'{paths.img_files}{paths.sep}spec.gif')

        except Exception as e:
            logger.info(f"функция play(self) в main.py, ошибка: {e}")

    async def orange_play_scenario(self,scenario_name):
        # self.initList()
        self.play_threads = []
        loop = 0
        volume = 100
        overload_value = 0
        filename = self.get_file_item_file_name()

        file_path = f"{paths.mp3_files}{paths.sep}{filename}"
        if not self.repeat_check_box.isChecked():
            loop = 1
        else:
            logger.info(loop)
            loop = str(self.repeat_spin_box.value())
        if self.volume_slider.value() <= 100:
            volume = str(self.volume_slider.value())
            overload_value = 0
        else:
            volume = 100
            overload_value = int(self.volume_slider.value()) - 100
        try:
            if file_path is not None:
                self.commit_orange_command_scenario(command="play",
                                           scenario_name=scenario_name,
                                           thread_list=self.play_threads,
                                           filename=file_path,
                                           text='',
                                           loop=loop,
                                           vol=volume,
                                           overload_value=overload_value
                                           )
                # self.now_playing.change_gif(f'{paths.img_files}{paths.sep}spec.gif')

        except Exception as e:
            logger.info(f"функция play(self) в main.py, ошибка: {e}")

    def orange_stop(self):
        """stop operations 2"""
        self.stop_threads.clear()
        try:
            self.commit_orange_command("stop", self.stop_threads)
        except Exception as e:
            logger.info(f"функция stop(self) в main.py, ошибка: {e}")

    def orange_stop(self):
        """stop operations 2"""
        self.stop_threads.clear()
        try:
            self.commit_orange_command("stop", self.stop_threads)
        except Exception as e:
            logger.info(f"функция stop(self) в main.py, ошибка: {e}")



    def orange_realtime(self):
        self.orange_stop()
        sleep(0.5)
        self.realtime_play_threads.clear()
        try:
            self.commit_orange_command("play_realtime",
                                       self.realtime_play_threads,
                                       is_rtp=True
                                       )
        except Exception as e:
            logger.info(f"функция realtime(self) в main.py, ошибка: {e}")

    def start_rtp_session(self, ip_list):
        if not ip_list:
            QMessageBox.warning(self, "Ошибка", "Не указаны IP-адреса зон")
            return

        # Остановка предыдущей трансляции
        if hasattr(self, 'audio_streamer') and self.audio_streamer:
            self.audio_streamer.stop()
            time.sleep(0.5)

        # Создание нового потока трансляции
        self.audio_streamer = AudioStreamer(ip_list)
        self.audio_streamer.rtp_process_message.connect(self.handle_streamer_message)
        self.audio_streamer.stream_status.connect(self.handle_stream_status)
        self.audio_streamer.start()

        # Визуальная индикация
        self.mic_usage_indicator.setVisible(True)
        self.mic_usage_indicator.change_gif(f'{paths.img_files}/mic.gif')

    def handle_streamer_message(self, msg):
        """Обработка сообщений от потока трансляции"""
        if "ошибка" in msg.lower():
            QMessageBox.warning(self, "Ошибка трансляции", msg)
            self.mic_usage_indicator.setVisible(False)

    def handle_stream_status(self, is_active):
        """Обработка изменения статуса трансляции"""
        self.is_streaming_flag = is_active
        if not is_active:
            self.mic_usage_indicator.setVisible(False)

    def orange_stop_realtime(self):
        """Остановка трансляции"""
        if hasattr(self, 'audio_streamer') and self.audio_streamer:
            self.audio_streamer.stop()
            self.audio_streamer = None

        # Остановка на устройствах
        self.commit_orange_command('stop_realtime', self.stop_realtime_threads)

    def orange_stop_realtime(self):
        if self.audio_streamer is not None:
            self.audio_streamer.baseRTP = RTP(
                marker=False,
                payloadType=PayloadType.L16_1chan,
                sequenceNumber=random.randint(0, 65535),
                timestamp=random.randint(0, 4294967295),
                ssrc=random.randint(0, 4294967295),
            )
            sleep(0.5)
            self.audio_streamer.stopFlag = True
            sleep(0.5)
            self.audio_streamer.stop()
            self.audio_streamer = None

        try:
            self.commit_orange_command('stop_realtime', self.stop_realtime_threads)

        except Exception as e:
            logging.error(f"функция stop_realtime(self) в main.py, ошибка: {e}")

    def do_rec(self):
        try:
            if self.recorder and self.recorder.isRunning():
                self.stop_recording()
            else:
                self.start_recording()
        except Exception as e:
            logging.error(f"Ошибка при записи с микрофона: {e}")

    @pyqtSlot(bytes)
    def on_new_audio_chunk(self, chunk):
        data_int = np.frombuffer(chunk, dtype=np.int16)
        # Вычисление среднего абсолютного значения для получения уровня громкости
        volume_level = np.mean(np.abs(data_int))
        print(int(volume_level))
        # Обновление прогрессбара
        self.volume_visualiser.setValue(round(volume_level))
        # Изменение цвета в зависимости от значения
        if volume_level < 21000:  # 70% от 30000
            color = "green"
        elif volume_level < 25500:  # 85% от 30000
            color = "yellow"
        else:
            color = "red"
        self.volume_visualiser.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}""")

    def start_recording(self):
        self.record_btn.setText('Остановить запись')

        self.recorder = Recorder()
        self.recorder.no_microphone_signal.connect(self.handle_no_microphone)
        self.recorder.new_data_signal.connect(self.on_new_audio_chunk)
        self.recorder.start()

        self.start_time = QTime(0, 0, 0)
        self.record_timer_label.setText(self.start_time.toString('hh:mm:ss'))
        self.timer_for_record.start(1000)

        self.mic_usage_indicator.change_gif(f'{paths.img_files}{paths.sep}mic.gif')
        self.progress_indicator.stopIndicate()
        self.mic_usage_indicator.setVisible(True)

    def update_record_timer(self):
        print("Таймер обновлен")
        self.app.processEvents()
        self.start_time = self.start_time.addSecs(1)
        self.record_timer_label.setText(self.start_time.toString('hh:mm:ss'))

    def stop_recording(self):
        self.record_btn.setText('Начать запись')
        self.mic_usage_indicator.setVisible(False)

        if self.timer_for_record.isActive():
            self.timer_for_record.stop()
            self.record_timer_label.setText("00:00:00")

        settings_dict = settings()
        iam_token = settings_dict["iam_token"]
        folder_id = settings_dict["folder_id"]

        wav_file_path = self.recorder.stop()  # wav
        ogg_file_path = f"{wav_file_path[:-4]}.ogg"

        self.progress_indicator.indicate()

        recognizer = Recognizer(iam_token, folder_id, wav_file_path, ogg_file_path)
        recognizer.result_signal.connect(self.handle_recognizer_result)
        recognizer.run()

    @pyqtSlot(dict, str)
    def handle_recognizer_result(self, result, ogg_file_path):
        """приходит ogg файл"""

        if result["result"] == '':
            recognize_text = self.handle_empty_recognition()
        else:
            recognize_text = result["result"]

        mp3_file_path = f"{ogg_file_path[:-4]}.mp3"
        mp3_file_name = os.path.basename(mp3_file_path)

        create_file_item_params = {
            "success": 1,  # 1 когда успешно, 0 когда не успешно
            "file_path": mp3_file_path,
            "file_name": mp3_file_name,
            "text": recognize_text,
            "voice": "Пользовательский",
        }

        """конвертируем в mp3 уже для хранения"""
        ffmpeg_t = FfmpegThread(
            input_file=ogg_file_path,
            output_file=mp3_file_path,
            params=create_file_item_params
        )
        ffmpeg_t.convert_finished.connect(self.on_ffmpeg_finished)
        ffmpeg_t.run()

        self.recorder = None

    def handle_empty_recognition(self):
        current_datetime = datetime.now()

        # Форматируем дату и время в формате dd.mm.yyyy HH:MM
        formatted_datetime = current_datetime.strftime('%d.%m.%Y %H:%M')
        recognize_text = f'запись с микрофона от {formatted_datetime}'
        return recognize_text

    @pyqtSlot(bool)
    def on_orange_finished(self, signal):
        if signal:
            self.progress_indicator.stopIndicate()

    @pyqtSlot(str)
    def on_orange_success(self, ip):
        """По идее должен собирать IP тех зон до которых достучались с командами"""
        self.success_IPs.append(ip)
        # self.progress_indicator.stopIndicate()
        logger.info(f"\nmain on_orange_success: список IP-{self.success_IPs}")

    def showSettingsDialog(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def select_voice_menu(self):
        menu = QMenu(self)
        voice1 = menu.addAction("мужской доброжелательный")
        voice2 = menu.addAction("женский доброжелательный")
        voice3 = menu.addAction("мужской нейтральный")
        voice4 = menu.addAction("женский нейтральный")

        voice1.triggered.connect(lambda: self.set_voice_params('мужской доброжелательный'))
        voice2.triggered.connect(lambda: self.set_voice_params('женский доброжелательный'))
        voice3.triggered.connect(lambda: self.set_voice_params('мужской нейтральный'))
        voice4.triggered.connect(lambda: self.set_voice_params('женский нейтральный'))

        button = self.sender()
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def set_voice_params(self, voice):
        self.selected_voice = voice
        self.selected_voice_text.setText(voice)

    def get_voice_params(self) -> tuple[str, str]:
        VOICE = ""
        EMOTION = ""
        if self.selected_voice == 'мужской доброжелательный':
            VOICE = 'filipp'
            EMOTION = 'good'

        if self.selected_voice == 'мужской нейтральный':
            VOICE = 'filipp'
            EMOTION = 'neutral'

        if self.selected_voice == 'женский доброжелательный':
            VOICE = 'alena'
            EMOTION = 'good'

        if self.selected_voice == 'женский нейтральный':
            VOICE = 'alena'
            EMOTION = 'neutral'

        return VOICE, EMOTION

    def set_light_theme(self):
        set_light_theme()
        self.apply_theme()

    def set_dark_theme(self):
        set_dark_theme()
        self.apply_theme()

    def init_menu_bar(self):
        self.statusBar()
        menu_bar = self.menuBar()

        pcn_action = QAction('PCN ID', self)
        pcn_action.triggered.connect(self.showSettingsDialog)

        light_theme_action = QAction('Светлая тема', self)
        light_theme_action.triggered.connect(self.set_light_theme)

        dark_theme_action = QAction('Темная тема', self)
        dark_theme_action.triggered.connect(self.set_dark_theme)

        set_view_menu = menu_bar.addMenu('&Вид')
        set_view_menu.addAction(light_theme_action)
        set_view_menu.addAction(dark_theme_action)

        settingsMenu = menu_bar.addMenu('&Настройки')
        settingsMenu.addAction(pcn_action)

    @pyqtSlot(int)
    def update_progress_bar(self, val):
        self.progressBar.setValue(val)
        self.app.processEvents()

    @pyqtSlot()
    def handle_no_microphone(self):
        print('no mic')
        self.progress_indicator.stopIndicate()
        self.mic_usage_indicator.setVisible(False)
        # self.now_playing.change_gif(f'{paths.img_files}{paths.sep}spec.gif')

        QMessageBox.information(self, 'Уведомление.',
                                'Похоже, у Вас не подключен микрофон. Подключите микрофон и повторите попытку')
        self.record_btn.setText('Начать запись')
        MainWindow.singleton = MainWindow(self.app, self.system_checker)

    def change_enabled_of_spin_box(self):
        if self.repeat_check_box.isChecked():
            self.repeat_spin_box.setEnabled(True)
            self.repeat_label.setEnabled(True)
        else:
            self.repeat_spin_box.setEnabled(False)
            self.repeat_label.setEnabled(False)

    def auto_search_zones(self):
        self.progressBar.setRange(0, 0)
        self.app.processEvents()
        result = subprocess.run(['bash', 'src/SCAN.sh'], stdout=subprocess.PIPE)
        output = result.stdout.decode()
        lines = output.splitlines()

        for line in lines:
            new_zone = Orange(
                ip=line,
                name=f"зона оповещения {line}",
                isChecked=True
            )
            self.zones_repo.add_zone(new_zone)

        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.app.processEvents()
        self.update_zones()

    def rename_zone(self, selected_zone: Orange):
        # selected_zone = self.zone_list_widget.get_current_zone()
        if selected_zone is not None:

            for zone in self.ZONE_LIST:
                if selected_zone.name == zone.name:
                    addZoneDialog = UI_AddZoneWindow(zone.name, zone.ip, self.ZONE_LIST, True)
                    if addZoneDialog.exec() == QDialog.Accepted:
                        zone.name = addZoneDialog.get_name_field().text()
                        zone.ip = addZoneDialog.get_ip_field().text()

            self.zones_repo.save(self.ZONE_LIST)

        self.update_zones()

    def add_zone_from_file(self, file_path):
        # Загрузка данных из файла
        self.zones_repo.add_zone_from_file(file_path)

        self.update_zones()
        sleep(0.1)

    def add_zone(self):
        addZoneDialog = UI_AddZoneWindow(f'зона {len(self.ZONE_LIST) + 1}', '192.168', self.ZONE_LIST)

        if addZoneDialog.exec() == QDialog.Accepted:
            logger.info(f"addZoneDialog.ip_field: {addZoneDialog.get_ip_field().text()}")
            logger.info(f"addZoneDialog.name_field: {addZoneDialog.get_name_field().text()}")
            ip_field = addZoneDialog.get_ip_field()
            name_field = addZoneDialog.get_name_field()

            new_zone = Orange(
                ip=ip_field.text(),
                name=name_field.text(),
                isChecked=True
            )

            if name_field.text() == "" or ip_field.text() == "":
                QMessageBox.information(self, 'Уведомление.',
                                        'Введите название зоны!')
            else:
                self.zones_repo.add_zone(new_zone)

        self.update_zones()

    def remove_zone(self, selected_zone: Orange):
        try:
            # selected_zone = self.zone_list_widget.get_current_zone()
            self.zones_repo.remove_zone(selected_zone)
            self.status_api.remove_broker(selected_zone.ip)
        except Exception as e:
            logging.error(f"main: remove_zone{e}")

        self.update_zones()

    #
    #
    def update_zones(self, status=None):
        if status:
            print(f"main: status on upd zonest {status}")

            self.status_sender.setStatus(status)
            # self.api_thread.start()

            self.update_zone_status(status)
        else:
            self.zone_list_widget.update_zones(self.ZONE_LIST)

            #self.update_ui()

    def update_zone_status(self, status):
        for zone in self.ZONE_LIST:
            if zone.ip == status.orange_ip:
                zone.is_playing = status.is_playing
                zone.is_streaming = status.is_streaming
                zone.is_sip_running = status.is_sip_running
                zone.is_online = self.status_api.is_online(status.orange_ip)
                zone.is_warning = "Error" in status.warn_message
                zone.tooltip_warn_message = status.warn_message
                zone.tooltip_message = status.message
        self.zone_list_widget.update_zones(self.ZONE_LIST)

    def update_ui(self):
        self.update_list_on_slider(self.grid_size)
        self.zone_list_widget.update_zones(self.ZONE_LIST)
        # self.setupUi(self)
        self.update()

    @pyqtSlot(OrangeStatus)
    def orange_status_receiver(self, status: OrangeStatus):
        """mqtt"""
        self.update_zones(status)

    def update_list_on_slider(self, val):
        self.grid_size = val
        self.update_file_list()
        logger.info(f"main: update_file_list_on_slider: {self.grid_size}")
        with open(grid, 'w') as f:
            f.write(str(val))

    def update_file_list(self, new_list: List[FileItem] = None):
        self.progress_indicator.stopIndicate()
        logger.info(f"main: update_file_list: {self.FILE_LIST}")

        if new_list:
            self.file_list_widget.update_file_list(new_list, self.grid_size)
        else:
            self.FILE_LIST = self.files_repo.file_list
            self.file_list_widget.update_file_list(self.FILE_LIST, self.grid_size)

    def sort_by_name(self):
        self.sort_key = 'header'
        self.name_reverse_key = not self.name_reverse_key
        icon = "sort2.png" if self.name_reverse_key else "sort1.png"
        self.sort_by_name_btn.setIcon(QIcon(f"{paths.img_files}/{icon}"))
        self.FILE_LIST = self.files_repo.sort_list(self.sort_key, self.name_reverse_key)
        self.update_file_list()

    def sort_by_date(self):
        self.sort_key = 'create_date'
        self.date_reverse_key = not self.date_reverse_key
        if self.date_reverse_key:
            self.sort_by_date_btn.setIcon(QIcon(f"{paths.img_files}/sort1.png"))
        else:
            self.sort_by_date_btn.setIcon(QIcon(f"{paths.img_files}/sort2.png"))

        self.FILE_LIST = self.files_repo.sort_list(self.sort_key, self.date_reverse_key)
        self.update_file_list()

    def on_search_changed(self, text: str):
        if not text:
            self.file_list_widget.update_file_list(self.FILE_LIST, self.grid_size)
        else:
            q = text.lower()
            filtered = [f for f in self.FILE_LIST if q in f.header.lower()]
            self.file_list_widget.update_file_list(filtered, self.grid_size)

    def play_file_local(self, file_item: FileItem):
        full_path_mp3_folder = os.path.join(os.getcwd(), mp3_files)
        full_path_to_mp3_file = os.path.join(full_path_mp3_folder, file_item.filename)
        logger.info(f"main: play_file_local {full_path_to_mp3_file}")

        if platform.system() == 'Windows':
            command = f"start wmplayer \"{full_path_to_mp3_file}\""
            os.system(command)
        else:
            # Экранируем специальные символы в имени файла
            escaped_path = shlex.quote(full_path_to_mp3_file)
            # Запускаем в фоновом режиме с помощью nohup и &
            command = f'nohup mplayer {escaped_path} > /dev/null 2>&1 &'
            subprocess.Popen(command, shell=True, close_fds=True)

    def delete_file(self, file_item: FileItem):

        logger.info(f"main: delete_file: {file_item}")
        self.FILE_LIST.remove(file_item)
        self.files_repo.remove_file(file_item)
        self.update_file_list(self.FILE_LIST)

    def rename_file(self, file_item: FileItem):
        for file in self.FILE_LIST:
            if file_item.filename == file.filename:
                dialog = Rename_Dialog(file_item.header)
                if dialog.exec() == QDialog.Accepted:
                    file.header = dialog.get_text()
                    self.files_repo.save()

        self.update_file_list()

    def add_description_to_file_item(self, file_item: FileItem):
        for file in self.FILE_LIST:
            if file_item == file:
                dialog = AddDescriptionDialog(file_item)
                if dialog.exec() == QDialog.Accepted:
                    file.text = dialog.get_text()
                    self.files_repo.save()
                self.update_file_list()

    def add_file_item(self, header, filename, text, current_voice):

        full_path_mp3_folder = os.path.join(os.getcwd(), mp3_files)
        full_path_to_mp3_file = os.path.join(full_path_mp3_folder, filename)
        audio = MP3(full_path_to_mp3_file)
        duration = audio.info.length
        create_time = get_creation_date(full_path_to_mp3_file)

        self.files_repo.add_file(
            FileItem(
                header=header,
                filename=filename,
                text=text,
                duration=round(duration),
                create_date=create_time,
                current_voice=current_voice
            )
        )

        self.update_file_list()

    def upload_custom_file(self):
        options = QFileDialog.Options()
        # options = QFileDialog.DontUseNativeDialog  # Не использовать нативный диалог на macOS

        if platform.system() == 'Windows':
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            download_dir = os.path.join(os.path.expanduser("~"), "Загрузки")

        # Отображение диалогового окна для выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", download_dir,
                                                   "MP3 files (*.mp3);",
                                                   options=options)
        if file_path:
            logger.info("upload_custom_file: Выбранный файл:", file_path)
            new_file_path = os.path.join(paths.mp3_files, os.path.basename(file_path))
            shutil.copy(file_path, new_file_path)
            audio = MP3(new_file_path)
            length = audio.info.length
            create_time = get_creation_date(new_file_path)
            new_file_item = FileItem(
                header=os.path.basename(new_file_path),
                filename=os.path.basename(new_file_path),
                text=f"Пользовательский файл из {file_path}",
                duration=round(length),
                create_date=create_time,
            )
            self.files_repo.add_file(new_file_item)
            # self.FILE_LIST.insert(0, new_file_item)
        self.update_file_list()

    def get_file_item_file_name(self) -> str:
        try:
            widget = self.file_list_widget.get_selected_file_item_widget()
            widget_file_name = widget.file_item.filename
            logger.info(widget_file_name)
            return widget_file_name
        except Exception as e:
            logger.info(e)

    @pyqtSlot(int)
    def progress_update(self, progress):
        self.progressBar.setValue(progress)
        logger.info(f"Прогресс выполнения: {progress}%")

    @pyqtSlot(str, dict)
    def on_ya_response(self, status_message, params):
        if status_message.find("ошибка") != -1:

            if platform.system() == 'Windows':
                self.progress_indicator.stopIndicate()
                QMessageBox.information(self, 'Не удалось озвучить текст',
                                        f" Нет соединения с интернетом: "
                                        f"\n{status_message}\n"
                                        )

            elif platform.system() == 'Linux':
                QMessageBox.information(self, 'Не удалось озвучить текст',
                                        f" Нет соединения с интернетом: "
                                        f"\n{status_message}\n"
                                        f"\nТекст будет озвучен локально, "
                                        f"голос может отличаться от выбранного."
                                        )

                # локальная озвучка
                mp3_file_name = params['file_name']
                full_path_mp3_folder = os.path.join(os.getcwd(), mp3_files)
                full_path_to_mp3_file = os.path.join(full_path_mp3_folder, mp3_file_name)
                full_path_to_wav_file = os.path.join(full_path_mp3_folder, f"{mp3_file_name[:-4]}.wav")
                text = params['text']
                #
                command = (f"echo '{text}' | "
                           f"RHVoice-test -R 48000 -p anna+CLB -r 100 -t 85 -v 130 -o - > {full_path_to_wav_file}")
                logger.info(f"command to rhvoice: {command}")
                subprocess.run(command, shell=True)

                ffmpeg_t = FfmpegThread(
                    input_file=full_path_to_wav_file,
                    output_file=full_path_to_mp3_file,
                    params=params
                )
                ffmpeg_t.convert_finished.connect(self.on_ffmpeg_finished)
                ffmpeg_t.run()

        if params["success"] == 1:
            self.add_file_item(
                params["text"],
                params["file_name"],
                params["text"],
                params["voice"]
            )

    def yandex_things(self):

        input_text = self.main_text_edit_field.toPlainText()

        if input_text != '':
            if len(input_text) < 250:
                settings_dict = settings()

                TOKEN = settings_dict["iam_token"]
                FOLDER_ID = settings_dict["folder_id"]
                VOICE, EMOTION = self.get_voice_params()
                TEXT = input_text.replace('//', '')
                short_voice = f"{VOICE[0]}{EMOTION[0]}"

                file_name_without_extension = f"{short_voice}{last_five_chars_of_datetime_timestamp()}_{self.main_text_edit_field.toPlainText()[:250]}"
                file_name = f"{sanitize_filename(file_name_without_extension)}.mp3"

                file_path = os.path.join(mp3_files, file_name)

                try:
                    yandex = YandexThread(
                        file_name=file_name,
                        file_path=file_path,
                        TEXT=TEXT,
                        TOKEN=TOKEN,
                        folder_id=FOLDER_ID,
                        VOICE=VOICE,
                        EMOTION=EMOTION
                    )
                    yandex.yandex_things_status.connect(self.on_ya_response)
                    yandex.run()

                except Exception as e:
                    logger.info(f"except {e}")
                    QMessageBox.information(self, 'Уведомление.', f'{e}:\n Нет соединения с интернетом. ')
            else:
                self.progress_indicator.stopIndicate()
                QMessageBox.information(self, 'Уведомление.',
                                        'похоже, Вы ввели слишком длинный текст. Пожалуйста, сократите текст до 250'
                                        'символов или разбейте текст на два файла')
        else:
            self.progress_indicator.stopIndicate()
            QMessageBox.information(self, 'Уведомление.', 'Введите текст для озвучки')

    @pyqtSlot(str, str)
    def tcp_orange_callback_status(self, msg, ip):
        QMessageBox.information(self, 'уведомление', f"{ip}\n{msg}")

    @pyqtSlot(bool)
    def handle_alarm_off(self, is_yes):
        """Приходит всегда когда заканчивается стрим"""
        if is_yes:
            self.mic_usage_indicator.setVisible(False)
            self.orange_stop()

    @pyqtSlot(str)
    def handle_some_msg(self, msg):
        """Общая функция для приема сообщений которые надо показать"""
        if msg.find("Ошибка в процессе трансляци") != -1:
            QMessageBox.information(self, 'уведомление', msg)

    @pyqtSlot(str, int)
    def indicate_file_played_on_orange(self, ip, duration):
        """Должен срабатывать на команде play когда приходит ответ от оранжа что File is playing"""
        # # self.now_playing.setVisible(True)
        # print('duration', duration)
        # QTimer.singleShot(duration * 1000, lambda: self.now_playing.setVisible(False))
        logger.info(f"main: indicate_file_played_on_orange: {ip}")

    @pyqtSlot(bool, dict)
    def on_ffmpeg_finished(self, success: bool, params: dict):
        if success:
            self.add_file_item(
                header=params["file_name"][:-4],
                filename=params["file_name"],
                text=params["text"],
                current_voice="пользовательский",
            )

    """Ивенты окна"""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            if file.endswith('.mp3'):
                try:

                    new_file_path = paths.mp3_files + os.sep + os.path.basename(file)
                    shutil.copy(file, new_file_path)
                    audio = MP3(file)
                    length = audio.info.length
                    create_time = get_creation_date(file)

                    self.files_repo.add_file(
                        FileItem(
                            header=os.path.basename(file),
                            filename=os.path.basename(file),
                            text=f"Пользовательский файл из {file}",
                            duration=round(length),
                            create_date=create_time,
                        )
                    )
                    self.update_file_list()
                except Exception as e:
                    if "are the same file" in str(e):
                        QMessageBox.information(self, 'уведомление', f'Этот файл уже есть в списке\n{e}')
                    else:
                        QMessageBox.information(self, 'уведомление', f'Файл который вы хотите добавить поврежден '
                                                                     f'или имеет недопустимые символы!\n{e}')
                    logger.info(f"Ошибка в процессе добавления файла: {e}")

            elif file.endswith('.json'):
                with open(file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Проверка наличия всех необходимых полей
                        if all(key in item for key in ('name', 'ip', 'isChecked')):
                            logger.info('JSON-файл содержит все необходимые поля')
                            self.add_zone_from_file(file)
                        else:
                            QMessageBox.information(self, 'уведомление',
                                                    'Не удалось распознать файл.')
                            logger.info('JSON-файл не содержит всех необходимых полей')
            else:
                QMessageBox.information(self, 'уведомление', 'Вы пытаетесь добавить неизвестный файл!')

    def apply_theme(self):
        with open(paths.settings) as s:
            app_theme = json.load(s)["theme"]

        from src.ui.theme import app_stylesheet
        self.app.setStyleSheet(app_stylesheet(app_theme))

        # Обновление интерфейса
        self.update_list_on_slider(self.grid_size)
        self.zone_list_widget.update_zones(self.ZONE_LIST)

        self.retranslate_ui(self)
        self.update_zones()
        self.update()

    def closeEvent(self, event: QEvent):
        self.perform_cleanup_actions()
        event.accept()

    def perform_cleanup_actions(self):
        for t in self.play_threads:
            t.terminate()
        logger.info('play_threads terminated')

        for t in self.stop_threads:
            t.terminate()
        logger.info('stop_threads terminated')

        for t in self.realtime_play_threads:
            t.terminate()
        logger.info('realtime_play_threads terminated')

        for t in self.stop_realtime_threads:
            t.terminate()
        logger.info('stop_realtime_threads terminated')

        for zone in self.ZONE_LIST:
            if zone.is_online:
                self.status_api.remove_broker(zone.ip)
                logger.info(f'{zone.ip}|{zone.name}: broker terminated')
            else:
                logger.info(f'{zone.ip}|{zone.name}: broker was offline')

        if self.connection_thread.isRunning():
            self.connection_thread.terminate()
            logger.info('connection_thread terminated')

        if self.is_streaming_flag:
            self.orange_stop_realtime()
            logger.info('Audio Stream terminated')

        # self.system_checker_thread.check_system()
        self.system_checker.terminate()
        logger.info('Application closing')

        # Завершаем приложение после завершения всех действий
        QApplication.instance().quit()


def except_hook(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog = QMessageBox()
    error_dialog.setWindowTitle("Ошибка")
    error_dialog.setWindowIcon(QIcon(f"{paths.img_files}{os.sep}logo (2).png"))

    # Создаем QTextEdit и устанавливаем его в качестве пользовательского виджета
    text_edit = QTextEdit()
    text_edit.setText(f"Произошла ошибка:\n{str(error_msg[:-200])}")
    text_edit.setReadOnly(True)  # Сделать его только для чтения
    text_edit.setFixedWidth(250)
    text_edit.setFixedHeight(200)
    error_dialog.layout().addWidget(text_edit)

    logging.error(f"Произошла ошибка:\n{error_msg}")
    print(f"Произошла ошибка:\n{error_msg}")
    error_dialog.exec_()


sys.excepthook = except_hook

logger = setup_logger()

#
def main():
    # Сначала проверяем блокировку до создания QApplication
    lock_file = 'app_lock.txt'

    # Проверка блокировки перед запуском
    if not check_lock(lock_file):
        # Создаем временное приложение для показа сообщения
        temp_app = QApplication(sys.argv)
        QMessageBox.critical(
            None,  # Родительское окно (None - без родителя)
            "Ошибка запуска",
            "Приложение уже запущено!\nПожалуйста, закройте предыдущую копию перед запуском новой.",
            QMessageBox.Ok
        )
        sys.exit(1)

    # Основное приложение
    app = QApplication(sys.argv)

    try:
        # Инициализация GUI
        loading_screen = LoadingScreen()
        loading_screen.show()

        # Создаем файл блокировки
        try:
            with open(lock_file, 'w') as f:
                timestamp = _time.time()
                f.write(str(timestamp))
            lock_logger.info(f"Файл блокировки создан: {timestamp}")
        except Exception as e:
            QMessageBox.critical(
                None,
                "Ошибка запуска",
                f"Не удалось создать файл блокировки:\n{str(e)}",
                QMessageBox.Ok
            )
            sys.exit(1)

        # Даем время для отображения загрузочного экрана
        QApplication.processEvents()

        # Создаем менеджер блокировки
        lock_manager = LockManager(lock_file)

        window = MainWindow(app)
        window.lock_manager = lock_manager  # Сохраняем ссылку на менеджер блокировки
        lock_manager.start()  # Запускаем обновление блокировки

        window.launch_system_checker()
        window.launch_status_connection()

        loading_screen.finish(window)
        window.show()

        return app.exec_()

    finally:
        # Гарантированная очистка блокировки при завершении
        lock_logger.info("Завершение приложения, очистка блокировки")
        if 'lock_manager' in locals():
            lock_manager.stop()
        else:
            # Если не удалось создать окно, все равно очищаем блокировку
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    lock_logger.info("Файл блокировки удален в блоке finally")
            except:
                pass


if __name__ == "__main__":
    main()