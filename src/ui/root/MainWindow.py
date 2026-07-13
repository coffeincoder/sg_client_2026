"""
MainWindow — главное окно приложения КСБ Саундгард.

Извлечено из main.py (Phase 0, Task 2).
main.py остаётся точкой входа; класс живёт здесь.
"""
import asyncio
import json
import logging
import os.path
import platform
import random
import shlex
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
import time as _time
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
from PyQt5.QtWidgets import (
    QAction, QMessageBox, QDialog, QMenu, QFileDialog, QApplication,
    QTextEdit, QPushButton, QComboBox, QHBoxLayout, QLabel, QTabWidget,
    QDesktopWidget,
)
from qtpy import QtWidgets
from rtp import RTP, PayloadType
from watchdog.observers import Observer

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

from src.utils.app_helpers import (
    convert_seconds, sanitize_filename, cut_filename,
    last_five_chars_of_datetime_timestamp, settings, mic_is_ready,
    set_light_theme, set_dark_theme,
)
from src.viewmodel.main_viewmodel import MainViewModel

logger = setup_logger()


class  MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, application):
        super(MainWindow, self).__init__()
        self.start_time = None

        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setAcceptDrops(True)
        self.setupUi(self)

        try:
            _root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except NameError:
            _root_dir = os.getcwd()
        _vfile = os.path.join(_root_dir, "VERSION")
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
        # sort_key / name_reverse_key / date_reverse_key переехали в FilesViewModel
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

        # Wire up ViewModel BEFORE signal connects so self.vm.files is available
        self.vm = MainViewModel(self)

        self.play_btn.clicked.connect(self.launch_play)
        self.stop_btn.clicked.connect(self.launch_stop)
        self.text_to_file_btn.clicked.connect(self.launch_yandex_process)
        self.zone_add_btn.clicked.connect(self.vm.zones.add_zone)

        self.auto_search_zones_btn.clicked.connect(self.vm.zones.auto_search_zones)
        self.zone_refresh_btn.clicked.connect(self.vm.zones.launch_status_connection)

        self.repeat_check_box.clicked.connect(self.change_enabled_of_spin_box)
        # Files signals → FilesViewModel
        self.sort_by_name_btn.clicked.connect(self.vm.files.sort_by_name)
        self.sort_by_date_btn.clicked.connect(self.vm.files.sort_by_date)
        self.search_input.textChanged.connect(self.vm.files.on_search_changed)
        self.upload_custom_file_btn.clicked.connect(self.vm.files.upload_custom_file)

        self.record_btn.clicked.connect(self.launch_rec)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.update_volume_on_oranges_btn.clicked.connect(self.send_new_volume_value)
        self.list_scale_slider.valueChanged.connect(self.vm.files.update_list_on_slider)
        self.voice_select_btn.clicked.connect(self.select_voice_menu)
        self.realtime_button.clicked.connect(self.launch_realtime)
        self.stop_realtime_button.clicked.connect(self.orange_stop_realtime)

        self.file_list_widget.delete_clicked.connect(self.vm.files.delete_file)
        self.file_list_widget.listen_clicked.connect(self.vm.files.play_file_local)
        self.file_list_widget.rename_clicked.connect(self.vm.files.rename_file)
        self.file_list_widget.add_description_clicked.connect(self.vm.files.add_description_to_file_item)

        self.zone_list_widget.rename_clicked.connect(self.vm.zones.rename_zone)
        self.zone_list_widget.delete_clicked.connect(self.vm.zones.remove_zone)

        self.waveform_viewer = VolumeVisualiser()

        self.set_volume()

        self.repeat_spin_box.setValue(5)

        self.mic_usage_indicator.setVisible(False)

        self.zones_repo = ZoneItemRepository()
        self.files_repo: FileItemRepository = FileItemRepository()

        self.FILE_LIST = self.files_repo.get()
        self.ZONE_LIST = self.zones_repo.all_zones

        self.status_api = StatusAPI(port=1883, topic="sg/statuses")
        self.status_api.status_changed.connect(self.vm.zones.orange_status_receiver)

        self.connection_thread = ConnectionThread(self.status_api, self.ZONE_LIST)
        self.connection_thread.connected.connect(self.vm.zones.on_connected)

        with open(paths.grid) as f:
            self.grid_size = int(f.read())
        self.list_scale_slider.setValue(self.grid_size)
        self.update_zones()
        self.update_list_on_slider(self.grid_size)
        self.system_checker: SystemChecker = SystemChecker(
            callback=self.vm.zones.update_statuses,
            check_interval=settings()["check_interval"]
        )
        self.init_menu_bar()
        self.apply_theme()
        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()

        # Устанавливаем размеры окна равными размерам экрана
        self.setGeometry(0, 0, width, height)
        self.sheduler = Scheduler(paths.shedule_data_scenaries, self.vm.scenarios.on_task_executed)
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

    def closeEvent(self, event):
        if self.lock_manager:
            self.lock_manager.stop()

        self.sheduler.terminate()
        self.observer.stop()
        self.observer.join()

        self.zone_list_widget.save_zones()
        event.accept()

    # --- Scenarios thin proxies (Task 5) ---

    def load_scenarios(self, *a, **k):
        return self.vm.scenarios.load_scenarios(*a, **k)


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

    # ------------------------------------------------------------------
    # Zones feature — thin View proxies delegating to ZonesViewModel.
    # launch_system_checker / launch_status_connection: called from main().
    # update_zones: called from __init__ and apply_theme.
    # update_online_status: connected as signal in commit_orange_command.
    # update_statuses: used as callback in SystemChecker constructor.
    # add_zone_from_file: called from dropEvent.
    # ------------------------------------------------------------------

    def launch_system_checker(self, *a, **k):
        return self.vm.zones.launch_system_checker(*a, **k)

    def launch_status_connection(self, *a, **k):
        return self.vm.zones.launch_status_connection(*a, **k)

    def update_online_status(self, *a, **k):
        return self.vm.zones.update_online_status(*a, **k)

    def update_statuses(self, *a, **k):
        return self.vm.zones.update_statuses(*a, **k)

    def on_connected(self, *a, **k):
        return self.vm.zones.on_connected(*a, **k)

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
                t.online_check.connect(self.vm.zones.update_online_status)
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
                t.online_check.connect(self.vm.zones.update_online_status)
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

    def auto_search_zones(self, *a, **k):
        return self.vm.zones.auto_search_zones(*a, **k)

    def rename_zone(self, *a, **k):
        return self.vm.zones.rename_zone(*a, **k)

    def add_zone_from_file(self, *a, **k):
        return self.vm.zones.add_zone_from_file(*a, **k)

    def add_zone(self, *a, **k):
        return self.vm.zones.add_zone(*a, **k)

    def remove_zone(self, *a, **k):
        return self.vm.zones.remove_zone(*a, **k)

    #
    #
    def update_zones(self, *a, **k):
        return self.vm.zones.update_zones(*a, **k)

    def update_zone_status(self, *a, **k):
        return self.vm.zones.update_zone_status(*a, **k)

    def update_ui(self, *a, **k):
        return self.vm.zones.update_ui(*a, **k)

    def orange_status_receiver(self, *a, **k):
        return self.vm.zones.orange_status_receiver(*a, **k)

    # ------------------------------------------------------------------
    # Files feature — thin View proxies delegating to FilesViewModel.
    # These proxies exist because the methods are called from non-Files
    # code that stays on the View (apply_theme, dropEvent, on_ya_response,
    # orange_play, on_ffmpeg_finished, yandex_things in __init__ block).
    # ------------------------------------------------------------------

    def update_list_on_slider(self, val, *args, **kwargs):
        return self.vm.files.update_list_on_slider(val, *args, **kwargs)

    def update_file_list(self, *args, **kwargs):
        return self.vm.files.update_file_list(*args, **kwargs)

    def add_file_item(self, *args, **kwargs):
        return self.vm.files.add_file_item(*args, **kwargs)

    def get_file_item_file_name(self, *args, **kwargs):
        return self.vm.files.get_file_item_file_name(*args, **kwargs)

    # These are also proxied to keep them callable via self.<method> from
    # any remaining internal code; signals already connect to vm.files directly.
    def sort_by_name(self, *args, **kwargs):
        return self.vm.files.sort_by_name(*args, **kwargs)

    def sort_by_date(self, *args, **kwargs):
        return self.vm.files.sort_by_date(*args, **kwargs)

    def on_search_changed(self, *args, **kwargs):
        return self.vm.files.on_search_changed(*args, **kwargs)

    def play_file_local(self, *args, **kwargs):
        return self.vm.files.play_file_local(*args, **kwargs)

    def delete_file(self, *args, **kwargs):
        return self.vm.files.delete_file(*args, **kwargs)

    def rename_file(self, *args, **kwargs):
        return self.vm.files.rename_file(*args, **kwargs)

    def add_description_to_file_item(self, *args, **kwargs):
        return self.vm.files.add_description_to_file_item(*args, **kwargs)

    def upload_custom_file(self, *args, **kwargs):
        return self.vm.files.upload_custom_file(*args, **kwargs)

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
