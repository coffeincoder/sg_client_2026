import logging
from typing import List

from PyQt5.QtCore import QThread, pyqtSignal

from src.data.ZoneModel import Orange
from src.utils.OrangeStatusAPI import StatusAPI

logger = logging.getLogger(__name__)

class ConnectionThread(QThread):
    connected = pyqtSignal()

    def __init__(self, status_api: StatusAPI, zone_list: List[Orange]):
        super().__init__()
        self.status_api = status_api
        self.zone_list = zone_list

    def run(self):
        for zone in self.zone_list:
            self.status_api.remove_broker(zone.ip)
            self.status_api.add_broker(zone.ip)
        self.connected.emit()  # После завершения операции подключения, мы посылаем сигнал
