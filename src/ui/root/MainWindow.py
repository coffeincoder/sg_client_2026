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
from PyQt5.QtGui import QIcon, QFont, QKeySequence
from PyQt5.QtWidgets import (
    QAction, QMessageBox, QDialog, QMenu, QFileDialog, QApplication,
    QTextEdit, QPushButton, QComboBox, QHBoxLayout, QLabel, QTabWidget,
    QDesktopWidget, QShortcut,
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
        self._tone_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        self._tone_shortcut.activated.connect(self.vm.playback.toggle_test_tone)

        self.play_btn.clicked.connect(self.vm.playback.launch_play)
        self.stop_btn.clicked.connect(self.vm.playback.launch_stop)
        self.text_to_file_btn.clicked.connect(self.vm.tts.launch_yandex_process)
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
        self.update_volume_on_oranges_btn.clicked.connect(self.vm.playback.send_new_volume_value)
        self.list_scale_slider.valueChanged.connect(self.vm.files.update_list_on_slider)
        self.voice_select_btn.clicked.connect(self.vm.tts.select_voice_menu)
        self.realtime_button.clicked.connect(self.vm.playback.launch_realtime)
        self.stop_realtime_button.clicked.connect(self.vm.playback.orange_stop_realtime)

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
            layout = self.zone_buttons_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(False)

        if index ==0:
            layout = self.zone_buttons_layout
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

    def send_new_volume_value(self, *a, **k):
        return self.vm.playback.send_new_volume_value(*a, **k)

    def launch_yandex_process(self, *a, **k):
        return self.vm.tts.launch_yandex_process(*a, **k)

    def launch_realtime(self, *a, **k):
        return self.vm.playback.launch_realtime(*a, **k)

    def launch_play(self, *a, **k):
        return self.vm.playback.launch_play(*a, **k)

    def launch_rec(self, *a, **k):
        return self.vm.recording.launch_rec(*a, **k)

    def launch_stop(self, *a, **k):
        return self.vm.playback.launch_stop(*a, **k)

    def commit_orange_command(self, *a, **k):
        return self.vm.playback.commit_orange_command(*a, **k)

    def commit_orange_command_scenario(self, *a, **k):
        return self.vm.playback.commit_orange_command_scenario(*a, **k)

    def on_streaming_status_changed(self, *a, **k):
        return self.vm.playback.on_streaming_status_changed(*a, **k)

    def on_thread_finished(self, *a, **k):
        return self.vm.playback.on_thread_finished(*a, **k)

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

    def orange_stop(self, *a, **k):
        return self.vm.playback.orange_stop(*a, **k)

    def orange_realtime(self, *a, **k):
        return self.vm.playback.orange_realtime(*a, **k)

    def start_rtp_session(self, *a, **k):
        return self.vm.playback.start_rtp_session(*a, **k)

    def handle_streamer_message(self, *a, **k):
        return self.vm.playback.handle_streamer_message(*a, **k)

    def handle_stream_status(self, *a, **k):
        return self.vm.playback.handle_stream_status(*a, **k)

    def orange_stop_realtime(self, *a, **k):
        return self.vm.playback.orange_stop_realtime(*a, **k)

    def do_rec(self, *a, **k):
        return self.vm.recording.do_rec(*a, **k)

    def on_new_audio_chunk(self, *a, **k):
        return self.vm.recording.on_new_audio_chunk(*a, **k)

    def start_recording(self, *a, **k):
        return self.vm.recording.start_recording(*a, **k)

    def update_record_timer(self, *a, **k):
        return self.vm.recording.update_record_timer(*a, **k)

    def stop_recording(self, *a, **k):
        return self.vm.recording.stop_recording(*a, **k)

    def handle_recognizer_result(self, *a, **k):
        return self.vm.recording.handle_recognizer_result(*a, **k)

    def handle_empty_recognition(self, *a, **k):
        return self.vm.recording.handle_empty_recognition(*a, **k)

    def on_orange_finished(self, *a, **k):
        return self.vm.playback.on_orange_finished(*a, **k)

    def on_orange_success(self, *a, **k):
        return self.vm.playback.on_orange_success(*a, **k)

    def showSettingsDialog(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def select_voice_menu(self, *a, **k):
        return self.vm.tts.select_voice_menu(*a, **k)

    def set_voice_params(self, *a, **k):
        return self.vm.tts.set_voice_params(*a, **k)

    def get_voice_params(self, *a, **k):
        return self.vm.tts.get_voice_params(*a, **k)

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

    def handle_no_microphone(self, *a, **k):
        return self.vm.recording.handle_no_microphone(*a, **k)

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

    # --- TTS thin proxies (Task 7) ---
    # progress_update: still connected from commit_orange_command /
    #   commit_orange_command_scenario (signal_progress_bar.connect(self.progress_update))
    # on_ffmpeg_finished: still connected from handle_recognizer_result
    #   (ffmpeg_t.convert_finished.connect(self.on_ffmpeg_finished))
    # yandex_things: still called from __init__ template-load block as
    #   self.yandex_things(data) — proxy forwards *a,**k verbatim (preserves
    #   the pre-existing arg-mismatch bug).
    # on_ya_response / select_voice_menu / set_voice_params / get_voice_params /
    #   launch_yandex_process: also proxied for any remaining callers.

    def progress_update(self, *a, **k):
        return self.vm.tts.progress_update(*a, **k)

    def on_ya_response(self, *a, **k):
        return self.vm.tts.on_ya_response(*a, **k)

    def yandex_things(self, *a, **k):
        return self.vm.tts.yandex_things(*a, **k)

    def on_ffmpeg_finished(self, *a, **k):
        return self.vm.tts.on_ffmpeg_finished(*a, **k)

    def tcp_orange_callback_status(self, *a, **k):
        return self.vm.playback.tcp_orange_callback_status(*a, **k)

    def handle_alarm_off(self, *a, **k):
        return self.vm.playback.handle_alarm_off(*a, **k)

    def handle_some_msg(self, *a, **k):
        return self.vm.playback.handle_some_msg(*a, **k)

    def indicate_file_played_on_orange(self, *a, **k):
        return self.vm.playback.indicate_file_played_on_orange(*a, **k)

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
