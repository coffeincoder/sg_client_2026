import logging
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.network.MqttClient import MqttStatusesSubscriber
from src.data.OrangeStatus import OrangeStatus

logger = logging.getLogger(__name__)


class MqttManager(QObject):
    """Хранит в себе всех слушателей(брокеров)"""
    status_updated = pyqtSignal(OrangeStatus)

    def __init__(self, port, topic):
        super().__init__()
        self._port = port
        self._topic = topic
        self._listeners: Dict[str, MqttStatusesSubscriber] = {}

    def add_broker(self, broker_ip: str):
        if broker_ip not in self._listeners:
            listener = MqttStatusesSubscriber(
                broker=broker_ip,
                port=self._port,
                topic=self._topic,
            )
            listener.message_received.connect(self.on_message_received)
            listener.connect()
            listener.start()
            self._listeners[broker_ip] = listener

    @pyqtSlot(OrangeStatus)
    def on_message_received(self, status: OrangeStatus):
        self.status_updated.emit(status)

    def remove_broker(self, broker_ip: str):
        if broker_ip in self._listeners:
            listener = self._listeners.pop(broker_ip)
            listener._client.loop_stop()
            listener._client.disconnect()

    def get_listener(self, broker_ip: str) -> MqttStatusesSubscriber:
        return self._listeners.get(broker_ip)
