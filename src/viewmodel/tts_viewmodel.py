"""
TtsViewModel — логика фичи «Озвучка/Yandex» (синтез речи Yandex, ffmpeg,
    выбор голоса, прогресс-бар).

Phase 2, Task 7: методы перенесены из MainWindow VERBATIM.
Виджеты и selected_voice доступны через self.view.<attr>.
TtsViewModel.__init__ ЛЁГКИЙ: только self.view.
"""
import os
import platform
import subprocess

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMenu, QMessageBox

import paths
from paths import mp3_files
from src.utils.FfmpegWork import FfmpegThread
from src.utils.Yandex import YandexThread
from src.utils.app_helpers import (
    last_five_chars_of_datetime_timestamp, sanitize_filename, settings,
)
from src.utils.logger_config import setup_logger

logger = setup_logger()


class TtsViewModel(QObject):
    """ViewModel для фичи «Озвучка/Yandex». Принимает ссылку на View для
    доступа к виджетам и selected_voice (остаётся на View)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # NOTE: self.view.selected_voice создаётся РАНЬШЕ в MainWindow.__init__
        # (до создания VM), поэтому не инициализируем здесь.

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM (self.<attr> → self.view.<attr>
    # для атрибутов/виджетов, принадлежащих View).
    # ------------------------------------------------------------------

    def launch_yandex_process(self):
        print('yandex')
        try:
            self.yandex_things()
        except Exception as e:
            logger.info(f"launch_yandex_process: {e}")

    def yandex_things(self):

        input_text = self.view.main_text_edit_field.toPlainText()

        if input_text != '':
            if len(input_text) < 250:
                settings_dict = settings()

                TOKEN = settings_dict["iam_token"]
                FOLDER_ID = settings_dict["folder_id"]
                VOICE, EMOTION = self.get_voice_params()
                TEXT = input_text.replace('//', '')
                short_voice = f"{VOICE[0]}{EMOTION[0]}"

                file_name_without_extension = f"{short_voice}{last_five_chars_of_datetime_timestamp()}_{self.view.main_text_edit_field.toPlainText()[:250]}"
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
                    QMessageBox.information(self.view, 'Уведомление.', f'{e}:\n Нет соединения с интернетом. ')
            else:
                self.view.progress_indicator.stopIndicate()
                QMessageBox.information(self.view, 'Уведомление.',
                                        'похоже, Вы ввели слишком длинный текст. Пожалуйста, сократите текст до 250'
                                        'символов или разбейте текст на два файла')
        else:
            self.view.progress_indicator.stopIndicate()
            QMessageBox.information(self.view, 'Уведомление.', 'Введите текст для озвучки')

    @pyqtSlot(str, dict)
    def on_ya_response(self, status_message, params):
        if status_message.find("ошибка") != -1:

            if platform.system() == 'Windows':
                self.view.progress_indicator.stopIndicate()
                QMessageBox.information(self.view, 'Не удалось озвучить текст',
                                        f" Нет соединения с интернетом: "
                                        f"\n{status_message}\n"
                                        )

            elif platform.system() == 'Linux':
                QMessageBox.information(self.view, 'Не удалось озвучить текст',
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
            self.view.add_file_item(
                params["text"],
                params["file_name"],
                params["text"],
                params["voice"]
            )

    def select_voice_menu(self):
        menu = QMenu(self.view)
        voice1 = menu.addAction("мужской доброжелательный")
        voice2 = menu.addAction("женский доброжелательный")
        voice3 = menu.addAction("мужской нейтральный")
        voice4 = menu.addAction("женский нейтральный")

        voice1.triggered.connect(lambda: self.set_voice_params('мужской доброжелательный'))
        voice2.triggered.connect(lambda: self.set_voice_params('женский доброжелательный'))
        voice3.triggered.connect(lambda: self.set_voice_params('мужской нейтральный'))
        voice4.triggered.connect(lambda: self.set_voice_params('женский нейтральный'))

        button = self.view.sender()
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def set_voice_params(self, voice):
        self.view.selected_voice = voice
        self.view.selected_voice_text.setText(voice)

    def get_voice_params(self) -> tuple:
        VOICE = ""
        EMOTION = ""
        if self.view.selected_voice == 'мужской доброжелательный':
            VOICE = 'filipp'
            EMOTION = 'good'

        if self.view.selected_voice == 'мужской нейтральный':
            VOICE = 'filipp'
            EMOTION = 'neutral'

        if self.view.selected_voice == 'женский доброжелательный':
            VOICE = 'alena'
            EMOTION = 'good'

        if self.view.selected_voice == 'женский нейтральный':
            VOICE = 'alena'
            EMOTION = 'neutral'

        return VOICE, EMOTION

    @pyqtSlot(int)
    def progress_update(self, progress):
        self.view.progressBar.setValue(progress)
        logger.info(f"Прогресс выполнения: {progress}%")

    @pyqtSlot(bool, dict)
    def on_ffmpeg_finished(self, success: bool, params: dict):
        if success:
            self.view.add_file_item(
                header=params["file_name"][:-4],
                filename=params["file_name"],
                text=params["text"],
                current_voice="пользовательский",
            )
