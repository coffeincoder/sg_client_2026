import threading
from time import sleep

import requests
import json
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
import logging

from src.data.OrangeStatus import OrangeStatus


#
class StatusSender(QThread):
    """Класс для отправки запроса к API в отдельном потоке."""

    signal_finished = pyqtSignal(bool, str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.statuses: list[OrangeStatus] = []
        self.session = None
        self.semaphore = threading.Semaphore()

    def send_status(self, status):
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.post(self.url, data=json.dumps(status.to_json()), headers=headers)
            response.raise_for_status()  # Проверка на ошибки
            print(f"StatusSender: status - ip:{status.orange_ip} unique_name: {status.orange_unique_name} message: {status.message}")
        except requests.RequestException as e:
            #self.signal_finished.emit(False, f"не удалось отправить статус\n")
            print(f"Ошибка при отправке статуса: {e}")

    def run(self):
        """Метод, который выполняется в отдельном потоке."""
        self.session = requests.Session()
        for status in self.statuses:
            with self.semaphore:
                self.send_status(status)
                # sleep(0.5)
                print(status)
        self.statuses.clear()
        self.session.close()
        self.quit()

    def setStatus(self, status):
        self.statuses.append(status)
