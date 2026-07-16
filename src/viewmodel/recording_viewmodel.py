"""
RecordingViewModel — логика фичи «Запись с микрофона» (AudioRecorder,
    таймер, распознавание речи, ffmpeg-конвертация).

Phase 2, Task 8: методы перенесены из MainWindow VERBATIM.
Все объекты, принадлежащие View (recorder, timer_for_record, start_time,
indication, indication_mic, waveform_viewer, app, system_checker), доступны
через self.view.<attr>.
RecordingViewModel.__init__ ЛЁГКИЙ: только self.view.
"""
import logging
import os
from datetime import datetime

import numpy as np
from PyQt5.QtCore import QObject, QTime, pyqtSlot
from PyQt5.QtWidgets import QMessageBox

import paths
from src.operations_with_files.AudioRecorder import Recorder
from src.utils.FfmpegWork import FfmpegThread
from src.utils.Recognizer import Recognizer
from src.utils.app_helpers import mic_is_ready, settings
from src.utils.logger_config import setup_logger

logger = setup_logger()


class RecordingViewModel(QObject):
    """ViewModel для фичи «Запись с микрофона». Принимает ссылку на View для
    доступа к виджетам и объектам записи (остаются на View)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # NOTE: self.view.recorder / timer_for_record / start_time / indication /
        # indication_mic / waveform_viewer создаются РАНЬШЕ в MainWindow.__init__
        # — не обращаться к ним здесь, только внутри методов.

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM (self.<attr> → self.view.<attr>
    # для атрибутов/виджетов, принадлежащих View; виджеты также через self.view).
    # ------------------------------------------------------------------

    def launch_rec(self):
        if not self.view.is_streaming_flag:
            self.view.progress_indicator.indicate()
            if mic_is_ready():
                self.do_rec()
            else:
                self.handle_no_microphone()

    def do_rec(self):
        try:
            if self.view.recorder and self.view.recorder.isRunning():
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
        self.view.volume_visualiser.setValue(round(volume_level))
        # Изменение цвета в зависимости от значения
        if volume_level < 21000:  # 70% от 30000
            color = "green"
        elif volume_level < 25500:  # 85% от 30000
            color = "yellow"
        else:
            color = "red"
        self.view.volume_visualiser.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}""")

    def start_recording(self):
        self.view.record_btn.setText('Остановить запись')

        self.view.recorder = Recorder()
        self.view.recorder.no_microphone_signal.connect(self.handle_no_microphone)
        self.view.recorder.new_data_signal.connect(self.on_new_audio_chunk)
        self.view.recorder.start()

        self.view.start_time = QTime(0, 0, 0)
        self.view.record_timer_label.setText(self.view.start_time.toString('hh:mm:ss'))
        self.view.timer_for_record.start(1000)

        self.view.mic_usage_indicator.change_gif(f'{paths.img_files}{paths.sep}mic.gif')
        self.view.progress_indicator.stopIndicate()
        self.view.mic_usage_indicator.setVisible(True)

    def update_record_timer(self):
        print("Таймер обновлен")
        self.view.app.processEvents()
        self.view.start_time = self.view.start_time.addSecs(1)
        self.view.record_timer_label.setText(self.view.start_time.toString('hh:mm:ss'))

    def stop_recording(self):
        self.view.record_btn.setText('Начать запись')
        self.view.mic_usage_indicator.setVisible(False)

        if self.view.timer_for_record.isActive():
            self.view.timer_for_record.stop()
            self.view.record_timer_label.setText("00:00:00")

        settings_dict = settings()
        iam_token = settings_dict["iam_token"]
        folder_id = settings_dict["folder_id"]

        wav_file_path = self.view.recorder.stop()  # wav
        ogg_file_path = f"{wav_file_path[:-4]}.ogg"

        self.view.progress_indicator.indicate()

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
        ffmpeg_t.convert_finished.connect(self.view.on_ffmpeg_finished)
        ffmpeg_t.run()

        self.view.recorder = None

    def handle_empty_recognition(self):
        current_datetime = datetime.now()

        # Форматируем дату и время в формате dd.mm.yyyy HH:MM
        formatted_datetime = current_datetime.strftime('%d.%m.%Y %H:%M')
        recognize_text = f'запись с микрофона от {formatted_datetime}'
        return recognize_text

    @pyqtSlot()
    def handle_no_microphone(self):
        print('no mic')
        self.view.progress_indicator.stopIndicate()
        self.view.mic_usage_indicator.setVisible(False)
        # self.now_playing.change_gif(f'{paths.img_files}{paths.sep}spec.gif')

        QMessageBox.information(self.view, 'Уведомление.',
                                'Похоже, у Вас не подключен микрофон. Подключите микрофон и повторите попытку')
        self.view.record_btn.setText('Начать запись')
        # NB: раньше здесь было `MainWindow.singleton = MainWindow(app, system_checker)` —
        # оно всегда падало TypeError (2 арг при __init__(self, application)), а `singleton`
        # нигде не читался. Пересоздавать окно при отсутствии микрофона не нужно: метод уже
        # сбросил индикаторы и показал сообщение. Строка удалена (баг был и до рефактора).
