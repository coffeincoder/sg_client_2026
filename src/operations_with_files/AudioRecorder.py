import logging
import os
import wave
from datetime import datetime
from time import sleep
#
import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal

import paths

logger = logging.getLogger(__name__)


class Recorder(QThread):
    stop_recording = pyqtSignal()
    no_microphone_signal = pyqtSignal()
    new_data_signal = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.stream = None
        self.p = None
        self.recording = False
        self.chunk = 1024  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1
        self.fs = 44100  # Record at 44100 samples per second

    def run(self):

        self.p = pyaudio.PyAudio()

        try:
            default_device_index = self.p.get_default_input_device_info()['index']
            self.stream = self.p.open(format=self.sample_format,
                                      channels=self.channels,
                                      rate=self.fs,
                                      frames_per_buffer=self.chunk,
                                      input=True,
                                      input_device_index=default_device_index)  # используем микрофон по умолчанию
        except Exception as e:
            self.no_microphone_signal.emit()  # отправка сигнала
            return

        self.frames = []
        self.recording = True

        while self.recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
                self.new_data_signal.emit(data)
            except Exception as e:
                logger.error(e)

    def stop(self) -> str:
        if self.recording:
            self.recording = False
            sleep(0.5)
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            filename = os.path.join(
                paths.mp3_files,
                f'запись с микрофона от {datetime.now().strftime("%Y-%m-%d_%H-%M-%S.wav")}'
            )
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.fs)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            return filename
