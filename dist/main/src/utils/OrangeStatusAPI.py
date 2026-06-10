from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.network.MqttManager import MqttManager
from src.data.OrangeStatus import OrangeStatus


class StatusAPI(QObject):
    """Orange статусы, связующий класс который нужно использовать для работы с интерфейсом"""
    status_changed = pyqtSignal(OrangeStatus)

    def __init__(self, port, topic):
        super().__init__()
        self._manager = MqttManager(port, topic)
        self._manager.status_updated.connect(self.on_status_updated)

    @pyqtSlot(OrangeStatus)
    def on_status_updated(self, status: OrangeStatus):
        self.status_changed.emit(status)

    def add_broker(self, broker_ip):
        self._manager.add_broker(broker_ip)

    def remove_broker(self, broker_ip):
        self._manager.remove_broker(broker_ip)

    def get_status(self, broker_ip):
        listener = self._manager.get_listener(broker_ip)
        if listener is not None:
            return listener.get_last_status()
        else:
            return None

    def is_online(self, broker_ip):
        listener = self._manager.get_listener(broker_ip)
        if listener is not None:
            return listener.is_online()
        else:
            return False

    def is_playing(self, broker_ip):
        status = self.get_status(broker_ip)
        return status.is_playing if status else False

    def is_streaming(self, broker_ip):
        status = self.get_status(broker_ip)
        return status.is_streaming if status else False

    def is_sip_running(self, broker_ip):
        status = self.get_status(broker_ip)
        return status.is_sip_running if status else False
