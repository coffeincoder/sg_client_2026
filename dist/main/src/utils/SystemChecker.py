import json
import logging
import os
import shutil
import time
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal

import paths
from paths import log_file
from src.utils.logger_config import setup_logger

logger = logging.getLogger(__name__)


class SystemChecker(QThread):
    def __init__(self, callback=None, check_interval=300):
        super(SystemChecker, self).__init__()
        self.callback = callback
        self.check_interval = check_interval

    def run(self):
        while True:
            time.sleep(self.check_interval)
            # time.sleep(5)
            try:
                self.check_system()
                self.create_new_log_file()
            except Exception as e:
                logger.info(e)
                print(f"SystemChecker error: {e}")

    def check_system(self):
        # Пример проверки системы
        logger.info("System check executed")
        self.callback()
        print("SystemChecker: check_system()")
        # todo: как-то реализовать проверку систем, например методы которые возвращают какой-то результат и
        #  записывать это результат в логгер

    def create_new_log_file(self):
        print(f"create_new_log_file init")
        log_file_path = paths.log_file
        if not os.path.isfile(log_file_path):
            return

        # Проверяем размер файла
        file_size = os.path.getsize(log_file_path)
        size_limit = 10 * 1024 * 1024  # 25 МБ в байтах
        print(f"create_new_log_file - fileSize: {file_size}")

        if file_size >= size_limit:
            print(f"create_new_log_file - file_size >= size_limit: {file_size >= size_limit}")
            logging.shutdown()

            # Получаем текущее время
            current_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            # Получаем новое имя файла
            base_name, ext = os.path.splitext(log_file_path)
            new_file_name = f"{base_name}_{current_date}{ext}"

            # Переименовываем файл
            shutil.move(log_file_path, new_file_name)
            print(f"Файл {log_file_path} переименован в {new_file_name}.")

            # Создаем новый пустой файл с исходным именем
            open(log_file_path, 'w').close()
            print(f"Создан новый пустой файл {log_file_path}.")

            setup_logger()

        else:
            print(f"Размер файла {log_file_path} меньше 25 МБ ({file_size} байт).")

