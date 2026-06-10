import json
import logging

import paho.mqtt.client as mqtt
from PyQt5.QtCore import QObject, pyqtSignal

from src.data.OrangeStatus import OrangeStatus

log_topic = "sg/logs"
status_topic = "sg/statuses"
log_port = 12346
statuses_port = 12345

logger = logging.getLogger(__name__)


class MqttStatusesSubscriber(QObject):
    message_received = pyqtSignal(OrangeStatus)

    def __init__(self, broker, port, topic):
        super().__init__()
        self._broker = broker
        self._port = port
        self._topic = topic
        self._client = mqtt.Client()
        self._client.username_pw_set(username="sg_user", password="orangepi")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self.last_status = None

    def _on_connect(self, client, userdata, flags, rc):
        logger.info("MqttStatusesSubscriber: Connected with result code " + str(rc))
        self._client.subscribe(self._topic)
        # connect_status = OrangeStatus(orange_ip=self._broker, message="online")
        # logger.info(f"MqttStatusesSubscriber._on_connect: {connect_status.message, connect_status.orange_ip}")
        # self.message_received.emit(connect_status)

    def _on_message(self, client, userdata, msg):
        logger.info(f'{msg.topic} {msg.payload}')
        message_data = json.loads(msg.payload)
        try:
            orange_status = OrangeStatus(
                orange_unique_id=message_data.get('orange_unique_id'),
                orange_unique_name=message_data.get('orange_unique_name'),
                orange_ip=message_data.get('orange_ip'),
                is_playing=message_data.get('is_playing'),
                current_file=message_data.get('current_file'),
                volume_value=message_data.get('volume_value'),
                start_time=message_data.get('start_time'),
                remaining_time=message_data.get('remaining_time'),
                user_priority=message_data.get('user_priority'),
                is_streaming=message_data.get('is_streaming'),
                is_sip_running=message_data.get('is_sip_running'),
                message=message_data.get('message')
            )
            logger.info(f"MqttStatusesSubscriber._onMessage: {orange_status.message, orange_status.orange_ip}")

            self.message_received.emit(orange_status)
            self.last_status = orange_status

        except Exception as e:
            logger.error(f"MqttStatusesSubscriber.ERROR _on_message: {e}")

        # todo: код для обработки полученных сообщений

    def connect(self):
        try:
            self._client.connect(self._broker, self._port, 60)
            logger.info(f"MqttStatusesSubscriber: Успешно подключено к брокеру {self._broker}")
        except Exception as e:
            self.message_received.emit(
                OrangeStatus(orange_ip=self._broker, warn_message=f"Error during connection: {e}"))
            logger.error(f"MqttStatusesSubscriber: Не удалось подключиться к брокеру {self._broker}. Ошибка: {e}")

    def start(self):
        self._client.loop_start()

    def get_last_status(self) -> OrangeStatus | None:
        return self.last_status

    def is_online(self) -> bool:
        """Возвращает True, если подключение к брокеру активно"""
        return self._client.is_connected()
