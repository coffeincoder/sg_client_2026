import logging
import subprocess

import ffmpeg
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class FfmpegThread(QThread):
    convert_finished = finished = pyqtSignal(bool, dict)

    def __init__(self, input_file, output_file, params: dict, bit_rate='64k'):
        super().__init__()
        logger.info(f"____FfmpegThread init")

        self.input_file = input_file  # полный путь
        self.output_file = output_file  # полный путь
        self.params = params
        self.bit_rate = bit_rate

    def run(self):

        logger.info(f"    input file {self.input_file}")
        logger.info(f"    output file {self.output_file}")
        command = [
            'ffmpeg',
            '-i', self.input_file,
            '-b:a', self.bit_rate,
            '-y',  # Overwrite output files without asking
            self.output_file
        ]
        try:
            subprocess.run(command, check=True)

            self.finished.emit(True, self.params)

            logger.info(f"____FfmpegThread finished {self.params} | {self.output_file}")
        except ffmpeg.Error as e:
            self.finished.emit(False, self.params)
            logger.info(f"____FfmpegThread error: {e} | {self.params} | {self.output_file}")
