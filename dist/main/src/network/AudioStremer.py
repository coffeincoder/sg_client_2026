import logging
import random
import socket
import time
from typing import List

import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal
from rtp import RTP, PayloadType

logger = logging.getLogger(__name__)


class AudioStreamer(QThread):
    rtp_process_message = pyqtSignal(str)
    stop_server = pyqtSignal(bool)
    stream_status = pyqtSignal(bool)

    def __init__(self, zones_ip):
        super().__init__()
        self.stop_flag = False
        self.zones_ip = zones_ip

        # Исходные параметры трансляции (без изменений)
        self.chunk = 1024  # Размер блока аудиоданных
        self.sample_rate = 44100  # Битрейт 44.1 kHz
        self.audio_format = pyaudio.paInt16  # 16-bit PCM
        self.channels = 1  # Моно

        self.audio = None
        self.stream = None
        self.sockets = []

    def run(self):
        if not self.zones_ip:
            self.rtp_process_message.emit("Ошибка: Не указаны IP-адреса зон")
            return

        try:
            # Инициализация аудиоустройства (без изменений параметров)
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk,
                input_device_index=self._get_input_device()
            )

            # Инициализация сокетов
            self.sockets = [self._create_socket(ip) for ip in self.zones_ip]

            # Инициализация RTP пакета (без изменений параметров)
            rtp_packet = RTP(
                marker=True,
                payloadType=PayloadType.L16_1chan,  # L16 как в исходной версии
                sequenceNumber=random.randint(0, 65535),
                timestamp=random.randint(0, 4294967295),
                ssrc=random.randint(0, 4294967295),
            )

            self.stream_status.emit(True)
            logger.info("Аудиотрансляция начата")

            while not self.stop_flag:
                try:
                    # Чтение аудиоданных
                    data = self.stream.read(self.chunk, exception_on_overflow=False)

                    # Обновление RTP пакета
                    rtp_packet.sequenceNumber += 1
                    rtp_packet.timestamp += self.chunk
                    rtp_packet.payload = bytearray(data)

                    # Отправка на все устройства
                    packet = rtp_packet.toBytearray()
                    for sock, ip in zip(self.sockets, self.zones_ip):
                        try:
                            sock.sendto(packet, (ip, 5000))
                        except socket.error as e:
                            logger.error(f"Ошибка отправки на {ip}: {e}")
                            self._reconnect_socket(sock, ip)

                    # Небольшая пауза для снижения нагрузки
                    time.sleep(0.005)

                except IOError as e:
                    logger.warning(f"Переполнение аудиобуфера: {e}")
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Ошибка трансляции: {e}")
                    time.sleep(1)

        except Exception as e:
            logger.critical(f"Фатальная ошибка трансляции: {e}")
            self.rtp_process_message.emit(f"Ошибка инициализации: {e}")
        finally:
            self._cleanup()
            self.stream_status.emit(False)
            logger.info("Аудиотрансляция остановлена")

    def _get_input_device(self):
        """Определение устройства ввода по умолчанию"""
        try:
            info = self.audio.get_default_input_device_info()
            return info['index']
        except:
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0:
                    return i
        return None

    def _create_socket(self, ip):
        """Создание UDP сокета с таймаутом"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        return sock

    def _reconnect_socket(self, sock, ip):
        """Переподключение сокета"""
        try:
            sock.close()
            new_sock = self._create_socket(ip)
            index = self.sockets.index(sock)
            self.sockets[index] = new_sock
            logger.info(f"Сокет для {ip} переподключен")
        except Exception as e:
            logger.error(f"Ошибка переподключения сокета: {e}")

    def _cleanup(self):
        """Очистка ресурсов"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Ошибка закрытия аудиопотока: {e}")
            self.stream = None

        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Ошибка освобождения аудиоресурсов: {e}")
            self.audio = None

        for sock in self.sockets:
            try:
                sock.close()
            except Exception as e:
                logger.error(f"Ошибка закрытия сокета: {e}")
        self.sockets = []

    def stop(self):
        """Остановка трансляции"""
        self.stop_flag = True
        if self.isRunning():
            self.wait(2000)  # Ожидание корректного завершения
            if self.isRunning():
                self.terminate()
        self._cleanup()