"""
PlaybackViewModel — логика фичи «Воспроизведение / Orange / Realtime Streaming».

Phase 2, Task 9: методы перенесены из MainWindow VERBATIM.
Состояние (play_threads, stop_threads, realtime_play_threads,
stop_realtime_threads, success_IPs, finished_threads, is_streaming_flag,
audio_streamer, status_sender) остаётся на View — доступ через self.view.<attr>.
PlaybackViewModel.__init__ ЛЁГКИЙ: только self.view.
"""
import asyncio
import logging
import os
import time

import random
from time import sleep

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon
from rtp import RTP, PayloadType

import paths
from src.network.AudioStremer import AudioStreamer
from src.network.OrangeWorkerTCP import OrangeWorkerTCP
from src.utils.app_helpers import mic_is_ready
from src.utils.logger_config import setup_logger
from src.viewmodel.channel_utils import active_channels, format_play_variant

logger = setup_logger()


def should_send_esp(file_esp):
    """Слать ли ESP-файл в сценарии: только при непустом имени."""
    return bool(file_esp and str(file_esp).strip())


def should_send_orange(file_obj):
    """Слать ли Orange-файл: только если объект файла есть и у него непустое имя."""
    return bool(file_obj is not None and getattr(file_obj, "filename", None))


class PlaybackViewModel(QObject):
    """ViewModel для фичи «Воспроизведение/Orange/Realtime».
    Принимает ссылку на View для доступа к виджетам и состоянию потоков
    (остаются на View)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # NOTE: self.view.play_threads / stop_threads / realtime_play_threads /
        # stop_realtime_threads / success_IPs / finished_threads /
        # is_streaming_flag / audio_streamer / status_sender
        # создаются в MainWindow.__init__ — не обращаться здесь, только внутри методов.

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM.
    # self.<attr> → self.view.<attr> для атрибутов View и виджетов.
    # self.vm.tts.progress_update → self.view.progress_update  (proxy)
    # self.vm.zones.update_online_status → self.view.update_online_status  (proxy)
    # self.load_scenarios() → self.view.load_scenarios()  (proxy)
    # Внутрифичевые вызовы (orange_stop, on_thread_finished, …) — self.<handler>.
    # ------------------------------------------------------------------

    def send_new_volume_value(self):
        self.commit_orange_command("vol", self.view.play_threads, vol=self.view.volume_slider.value())

    def launch_realtime(self):
        if not self.view.is_streaming_flag:
            if mic_is_ready():
                self.orange_realtime()
            else:
                self.view.handle_no_microphone()

    def launch_play(self):
        if not self.view.is_streaming_flag:

            index = self.view.filelist_tab_widget.currentIndex()
            if index==0:
                asyncio.run(self.view.orange_play())
            if index==1:

                scenario_name = self.view.layout_manager.main_window.scenario_listwidget.currentItem().text()
                print(scenario_name)
                asyncio.run(self.view.orange_play_scenario(scenario_name=scenario_name))

    def launch_stop(self):
        """stop operations 1"""
        if not self.view.is_streaming_flag:
            self.view.progress_indicator.indicate()
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
            is_rtp=False,
            mode='file'
    ):
        if is_rtp:
            logger.info("__RTP")
        else:
            logger.info(f"common orange command - {command}")
        zones = self.view.ZONE_LIST

        self.view.realtime_play_threads.clear()
        self.view.stop_realtime_threads.clear()
        self.view.play_threads.clear()
        self.view.stop_threads.clear()
        self.view.success_IPs.clear()

        for zone in zones:
            if zone.isChecked:
                self.view.progress_indicator.indicate()
                logger.info(f"commit_command({command}): зона '{zone.name}|{zone.ip}' установлена")
                print(command)

                _play_variant = format_play_variant(active_channels(zone))


                t = OrangeWorkerTCP(
                    command=command,
                    ip=str(zone.ip),
                    text=text,
                    loop=loop,
                    file_path=filename,
                    vol=vol,
                    overload_value=overload_value,
                    play_variant=_play_variant,
                    mode=mode
                )

                t.signal.connect(self.indicate_file_played_on_orange)  # подключите функцию, которая обновит GUI
                t.status.connect(self.tcp_orange_callback_status)
                t.signal_progress_bar.connect(self.view.progress_update)
                t.success_rtp_signal.connect(self.on_orange_success)
                t.final_signal.connect(self.on_orange_finished)
                t.online_check.connect(self.view.update_online_status)
                thread_list.append(t)
                logger.info(
                    f"commit_command({command}): список потоков для команды ({len(thread_list)}) : {thread_list}")

        if command != 'vol':
            self.view.mic_usage_indicator.setVisible(False)

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
            is_rtp=False,
            mode='scenario'
    ):
        if is_rtp:
            logger.info("__RTP")
        else:
            logger.info(f"common orange command - {command}")
        zones = self.view.ZONE_LIST
        print('11111111111111111111111111')
        self.view.realtime_play_threads.clear()
        self.view.stop_realtime_threads.clear()
        self.view.play_threads.clear()
        self.view.stop_threads.clear()
        self.view.success_IPs.clear()
        scenarios=self.view.load_scenarios()
        print(scenario_name)
        specific_scenario = scenarios.get(scenario_name)
        print(specific_scenario)
        if specific_scenario:
            for item in specific_scenario.ScenarioItems:
                print(item)
                # Получаем объект Orange
                print(item.zone.ip)
                print(item.file.filename if should_send_orange(item.file) else None)

                #self.progress_indicator.indicate()
                #logger.info(f"commit_command({command}): зона '{zone.name}|{zone.ip}' установлена")
                if should_send_orange(item.file):
                    t = OrangeWorkerTCP(
                        command=command,
                        ip=str(item.zone.ip),
                        text=text,
                        loop=loop,
                        file_path=os.path.join(paths.mp3_files, item.file.filename),
                        vol=vol,
                        overload_value=overload_value,
                        mode=mode
                    )

                    t.signal.connect(self.indicate_file_played_on_orange)  # подключите функцию, которая обновит GUI
                    t.status.connect(self.tcp_orange_callback_status)
                    t.signal_progress_bar.connect(self.view.progress_update)
                    t.success_rtp_signal.connect(self.on_orange_success)
                    t.final_signal.connect(self.on_orange_finished)
                    t.online_check.connect(self.view.update_online_status)
                    thread_list.append(t)

                esp_filename = getattr(item, "file_esp_filename", None)
                if should_send_esp(esp_filename):
                    esp_worker = OrangeWorkerTCP(
                        command='play_esp',
                        ip=str(item.zone.ip),
                        text=text,
                        loop=loop,
                        file_path=os.path.join(paths.mp3_files, esp_filename),
                        vol=vol,
                        overload_value=overload_value,
                    )
                    thread_list.append(esp_worker)

                logger.info(
                    f"commit_command({command}): список потоков для команды ({len(thread_list)}) : {thread_list}")

            if command != 'vol':
                self.view.mic_usage_indicator.setVisible(False)

            for thread in thread_list:
                logger.info(f"commit_command({command}): поток {thread} запущен")
                thread.start()
                if is_rtp:
                    thread.finished.connect(self.on_thread_finished)

    @pyqtSlot(bool)
    def on_streaming_status_changed(self, is_streaming: bool):
        """Подключен к AudioStreamer и получает сигнал либо о старте трансляции либо об остановке"""
        self.view.is_streaming_flag = is_streaming
        if is_streaming:
            self.view.stop_realtime_button.setIcon(QIcon(paths.img_files + os.sep + "broadcast-off-red.png"))
        else:
            self.view.stop_realtime_button.setIcon(QIcon(paths.img_files + os.sep + "broadcast-off-custom.png"))

    def on_thread_finished(self):
        self.view.finished_threads += 1
        if self.view.finished_threads == len(self.view.realtime_play_threads):
            self.start_rtp_session(self.view.success_IPs)
            self.view.finished_threads = 0

    def orange_stop(self):
        """stop operations 2"""
        self.view.stop_threads.clear()
        try:
            self.commit_orange_command("stop", self.view.stop_threads)
        except Exception as e:
            logger.info(f"функция stop(self) в main.py, ошибка: {e}")

    def orange_realtime(self):
        self.orange_stop()
        sleep(0.5)
        self.view.realtime_play_threads.clear()
        try:
            self.commit_orange_command("play_realtime",
                                       self.view.realtime_play_threads,
                                       is_rtp=True
                                       )
        except Exception as e:
            logger.info(f"функция realtime(self) в main.py, ошибка: {e}")

    def start_rtp_session(self, ip_list):
        if not ip_list:
            QMessageBox.warning(self.view, "Ошибка", "Не указаны IP-адреса зон")
            return

        # Остановка предыдущей трансляции
        if hasattr(self.view, 'audio_streamer') and self.view.audio_streamer:
            self.view.audio_streamer.stop()
            time.sleep(0.5)

        # Создание нового потока трансляции
        self.view.audio_streamer = AudioStreamer(ip_list)
        self.view.audio_streamer.rtp_process_message.connect(self.handle_streamer_message)
        self.view.audio_streamer.stream_status.connect(self.handle_stream_status)
        self.view.audio_streamer.start()

        # Визуальная индикация
        self.view.mic_usage_indicator.setVisible(True)
        self.view.mic_usage_indicator.change_gif(f'{paths.img_files}/mic.gif')

    def handle_streamer_message(self, msg):
        """Обработка сообщений от потока трансляции"""
        if "ошибка" in msg.lower():
            QMessageBox.warning(self.view, "Ошибка трансляции", msg)
            self.view.mic_usage_indicator.setVisible(False)

    def handle_stream_status(self, is_active):
        """Обработка изменения статуса трансляции"""
        self.view.is_streaming_flag = is_active
        if not is_active:
            self.view.mic_usage_indicator.setVisible(False)

    def orange_stop_realtime(self):
        if self.view.audio_streamer is not None:
            self.view.audio_streamer.baseRTP = RTP(
                marker=False,
                payloadType=PayloadType.L16_1chan,
                sequenceNumber=random.randint(0, 65535),
                timestamp=random.randint(0, 4294967295),
                ssrc=random.randint(0, 4294967295),
            )
            sleep(0.5)
            self.view.audio_streamer.stopFlag = True
            sleep(0.5)
            self.view.audio_streamer.stop()
            self.view.audio_streamer = None

        try:
            self.commit_orange_command('stop_realtime', self.view.stop_realtime_threads)

        except Exception as e:
            logging.error(f"функция stop_realtime(self) в main.py, ошибка: {e}")

    @pyqtSlot(bool)
    def on_orange_finished(self, signal):
        if signal:
            self.view.progress_indicator.stopIndicate()

    @pyqtSlot(str)
    def on_orange_success(self, ip):
        """По идее должен собирать IP тех зон до которых достучались с командами"""
        self.view.success_IPs.append(ip)
        # self.progress_indicator.stopIndicate()
        logger.info(f"\nmain on_orange_success: список IP-{self.view.success_IPs}")

    @pyqtSlot(str, str)
    def tcp_orange_callback_status(self, msg, ip):
        QMessageBox.information(self.view, 'уведомление', f"{ip}\n{msg}")

    @pyqtSlot(bool)
    def handle_alarm_off(self, is_yes):
        """Приходит всегда когда заканчивается стрим"""
        if is_yes:
            self.view.mic_usage_indicator.setVisible(False)
            self.orange_stop()

    @pyqtSlot(str)
    def handle_some_msg(self, msg):
        """Общая функция для приема сообщений которые надо показать"""
        if msg.find("Ошибка в процессе трансляци") != -1:
            QMessageBox.information(self.view, 'уведомление', msg)

    @pyqtSlot(str, int)
    def indicate_file_played_on_orange(self, ip, duration):
        """Должен срабатывать на команде play когда приходит ответ от оранжа что File is playing"""
        # # self.now_playing.setVisible(True)
        # print('duration', duration)
        # QTimer.singleShot(duration * 1000, lambda: self.now_playing.setVisible(False))
        logger.info(f"main: indicate_file_played_on_orange: {ip}")
