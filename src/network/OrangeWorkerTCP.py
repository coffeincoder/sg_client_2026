import hashlib
import json
import logging
import os
import socket
from PyQt5.QtCore import pyqtSignal, QThread
from mutagen.mp3 import MP3
import paths

BUFFER_SIZE = 1024
logger = logging.getLogger(__name__)


def calculate_crc(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_mp3_duration(file_path):
    audio = MP3(file_path)
    duration = int(audio.info.length)
    return duration


def create_socket(ip, port, timeout):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(timeout)
    server_address = (ip, port)
    client_socket.connect(server_address)
    return client_socket


def send_command(client_socket, command, ip=None):
    json_command = json.dumps(command)
    logger.info(f"    send_command - {json_command}")
    client_socket.sendall(json_command.encode())
    data = client_socket.recv(BUFFER_SIZE)
    return data.decode()


def create_simple_command(ip, port, timeout, command):
    message = ""
    try:
        with create_socket(ip, port, timeout) as client_socket:
            client_socket.settimeout(5)
            response = send_command(client_socket, command, ip)
            message = response
            logger.info(f"    create_simple_command ({command}): response - {message}")

            # Проверяем специальное сообщение о разряженной батарее
            if message == 'battery_low':
                return 'battery_low'

    except Exception as e:
        message = f"Не удалось выполнить команду {command['command']}: {e}"
        logger.info(f"    create_simple_command: response - {message}")

    return message


class OrangeWorkerTCP(QThread):
    status = pyqtSignal(str, str)
    signal = pyqtSignal(str, int)
    signal_progress_bar = pyqtSignal(int)
    success_rtp_signal = pyqtSignal(str)
    final_signal = pyqtSignal(bool)
    online_check = pyqtSignal(bool, str)

    def __init__(self, command, ip, text, file_path=None, loop=None, vol=None, overload_value=None, play_variant=None):
        QThread.__init__(self)
        self.command = command
        self.ip = ip
        self.file_path = file_path
        self.loop = loop
        self.vol = vol
        self.timeout = None
        self.text = text
        self.overload_value = overload_value
        self.play_variant = play_variant

    def emit_status(self, msg, ip):
        self.status.emit(msg, ip)

    def emit_signal(self, msg, duration: int):
        self.signal.emit(msg, duration)

    def emit_signal_progress_bar(self, progress: int):
        self.signal_progress_bar.emit(progress)

    def work(self, ip, port):
        with open(paths.tcp_timeout) as f:
            self.timeout = int(f.read())

        if self.command == "status":
            status_response = create_simple_command(ip, port, self.timeout, {"command": "hello"})
            if status_response.find("Wrong command") != -1 or status_response.find("OK") != -1:
                self.online_check.emit(True, self.ip)
            else:
                self.online_check.emit(False, self.ip)

        if self.play_variant is not None:
            create_simple_command(ip, port, self.timeout,
                                  {"command": 'play_variant', "value": str(self.play_variant)})

        if self.command == "vol":
            create_simple_command(ip, port, self.timeout,
                                  {"command": 'vol', "value": str(self.vol),
                                   "overload_value": str(self.overload_value)})

        if self.command == 'play':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find('Server is playing now') != -1 or status_response.find(
                    'Server is streaming now') != -1:
                self.emit_status(f'Выбранное устройство уже занято, подождите!', self.ip)
                return
            elif status_response.find("Не удалось") != -1:
                raise socket.error("Не удалось достучаться до оранжа")
            else:
                create_simple_command(ip, port, self.timeout,
                                      {"command": 'vol', "value": str(self.vol),
                                       "overload_value": str(self.overload_value)})
                create_simple_command(ip, port, self.timeout,
                                      {"command": 'loop', "value": str(self.loop)})

                loaded = self.load_file(ip, port, self.file_path)
                if not loaded:
                    return

                with create_socket(ip, port, self.timeout) as client_socket:
                    client_socket.settimeout(5)
                    response = send_command(client_socket,
                                            {"command": 'play', "filename": os.path.basename(self.file_path)},
                                            ip)

                    if response == 'battery_low':
                        self.emit_status("АКБ разряжен! Сообщите нам об этом позвонив по номеру 404290", self.ip)
                        return
                    elif response.find('File is playing') != -1:
                        duration = get_mp3_duration(self.file_path)
                        duration = duration * int(self.loop)
                        duration = duration + (2 * int(self.loop)) + 2
                        self.emit_signal(str(ip), duration)
                    elif response.find('err: device busy') != -1:
                        self.emit_status("ошибка: устройство занято", self.ip)
        if self.command == 'stop_esp':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find("Не удалось") != -1:
                raise socket.error()
            else:
                create_simple_command(ip, port, self.timeout, {"command": "stop_esp"})

        if self.command == 'play_esp':

            loaded = self.load_file_esp(ip, port, self.file_path,self.loop)
            if not loaded:
                return

            with create_socket(ip, port, self.timeout) as client_socket:
                client_socket.settimeout(5)
                response = send_command(client_socket,
                                        {"command": 'play_esp', "filename": os.path.basename(self.file_path), "loop": str(self.loop)},
                                        ip)



        if self.command == 'stop':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find("Не удалось") != -1:
                raise socket.error()
            else:
                create_simple_command(ip, port, self.timeout, {"command": "stop"})

        if self.command == 'stop_esp':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find("Не удалось") != -1:
                raise socket.error()
            else:
                create_simple_command(ip, port, self.timeout, {"command": "stop_esp"})

        if self.command == 'play_realtime':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find("Не удалось") != -1:
                raise socket.error()
            elif status_response.find("Server is streaming now") == -1:
                start_response = create_simple_command(ip, port, self.timeout, {"command": "play_realtime"})
                if start_response.find("RTP Server failed") != -1:
                    logger.info(f"OrangeWorkerTCP play_realtime: {start_response}")
                    self.emit_status("Не удалось начать трансяцию", self.ip)
                elif start_response.find("RTP Server Started") != -1:
                    logger.info(f"OrangeWorkerTCP play_realtime: {start_response}")
                    self.success_rtp_signal.emit(self.ip)

        if self.command == 'stop_realtime':
            status_response = create_simple_command(ip, port, self.timeout, {"command": 'status'})
            if status_response.find("Не удалось") != -1:
                raise socket.error()
            else:
                stop_response = create_simple_command(ip, port, self.timeout, {"command": "stop_realtime"})

    def load_file(self, ip, port, file_path):
        counter_try = 0
        with open(paths.crc_try) as f:
            crc_try = int(f.read())

        success = False
        while counter_try <= crc_try:
            try:
                message = {
                    "command": 'load',
                    "filename": str(os.path.basename(file_path)),
                    "filesize": str(os.path.getsize(file_path)),
                    "crc": str(calculate_crc(file_path))

                }

                sock = create_socket(ip, port, self.timeout)
                first_load_response = send_command(sock, message)

                if first_load_response == 'Ready to receive file\n':
                    server_response = "Chunk received successfully\n"
                    len_file = os.path.getsize(file_path)
                    len_parts = int(len_file // BUFFER_SIZE)

                    with open(file_path, 'rb') as file:
                        counter = 0
                        while True:
                            counter = counter + 1
                            chunk = file.read(BUFFER_SIZE)
                            if not chunk:
                                logger.info("not chunk")
                                break

                            if server_response == "Chunk received successfully\n":
                                per = (counter / len_parts) * 100
                                self.emit_signal_progress_bar(int(per))
                                sock.sendall(chunk)
                            else:
                                raise socket.timeout

                            server_response = sock.recv(BUFFER_SIZE).decode()
                        self.emit_signal_progress_bar(0)

                    if server_response == "File received successfully\n":
                        logger.info(f"    File uploaded successfully после загрузки")
                        self.emit_signal_progress_bar(0)
                        success = True
                        return success

                    elif server_response.find("Failed to convert") != -1:
                        msg = f"    1 Не удалось воспроизвести {file_path}. Запишите файл еще раз и повторите попытку "
                        self.emit_status(msg, ip)
                        success = False
                        return success

                    elif server_response == "crc_error\n":
                        raise socket.timeout

                elif first_load_response == "File has already been uploaded\n":
                    second_load_response = sock.recv(BUFFER_SIZE).decode()

                    if second_load_response == "File received successfully\n":
                        logger.info("    File uploaded successfully файл уже был загружен но не конвертирован")
                        success = True
                        return success

                    elif second_load_response.find("Failed to convert") != -1:
                        msg = f"    2 Не удалось воспроизвести {file_path}. Запишите сценарий еще раз и повторите попытку "
                        self.emit_status(msg, ip)
                        success = False
                        return success

                elif first_load_response == "File received successfully\n":
                    success = True
                    return success

                elif first_load_response == "crc_error\n":
                    raise socket.timeout

            except socket.timeout as e:
                counter_try += 1
                if counter_try > crc_try:
                    msg = f"    Проблемы с сетью, попробуйте еще раз: {e}"
                    logging.error(msg)
                    self.emit_status(msg, ip)
                    success = False

            except socket.error as e:
                msg = f"    Загрузка файла была прервана, пожалуйста, проверьте подключение к сети и повторите попытку: {e}"
                logging.error(msg)
                self.emit_status(msg, ip)
                success = False
                break

            except Exception as e:
                msg = f"    произошла неизвестная ошибка, повторите попытку: {e}"
                logging.error(msg)
                self.emit_status(msg, ip)
                return False

        if counter_try >= crc_try:
            sock.close()
            return success


    def load_file_esp(self, ip, port, file_path,loop):
        counter_try = 0
        with open(paths.crc_try) as f:
            crc_try = int(f.read())

        success = False
        while counter_try <= crc_try:
            try:
                message = {
                    "command": 'load_esp',
                    "filename": str(os.path.basename(file_path)),
                    "filesize": str(os.path.getsize(file_path)),
                    "crc": str(calculate_crc(file_path)),
                    "loop": str(loop)
                }

                sock = create_socket(ip, port, self.timeout)
                first_load_response = send_command(sock, message)

                if first_load_response == 'Ready to receive file\n':
                    server_response = "Chunk received successfully\n"
                    len_file = os.path.getsize(file_path)
                    len_parts = int(len_file // BUFFER_SIZE)

                    with open(file_path, 'rb') as file:
                        counter = 0
                        while True:
                            counter = counter + 1
                            chunk = file.read(BUFFER_SIZE)
                            if not chunk:
                                logger.info("not chunk")
                                break

                            if server_response == "Chunk received successfully\n":
                                per = (counter / len_parts) * 100
                                self.emit_signal_progress_bar(int(per))
                                sock.sendall(chunk)
                            else:
                                raise socket.timeout

                            server_response = sock.recv(BUFFER_SIZE).decode()
                        self.emit_signal_progress_bar(0)

                    if server_response == "File received successfully\n":
                        logger.info(f"    File uploaded successfully после загрузки")
                        self.emit_signal_progress_bar(0)
                        success = True
                        return success

                    elif server_response.find("Failed to convert") != -1:
                        msg = f"    1 Не удалось воспроизвести {file_path}. Запишите файл еще раз и повторите попытку "
                        self.emit_status(msg, ip)
                        success = False
                        return success

                    elif server_response == "crc_error\n":
                        raise socket.timeout

                elif first_load_response == "File has already been uploaded\n":
                    second_load_response = sock.recv(BUFFER_SIZE).decode()

                    if second_load_response == "File received successfully\n":
                        logger.info("    File uploaded successfully файл уже был загружен но не конвертирован")
                        success = True
                        return success

                    elif second_load_response.find("Failed to convert") != -1:
                        msg = f"    2 Не удалось воспроизвести {file_path}. Запишите сценарий еще раз и повторите попытку "
                        self.emit_status(msg, ip)
                        success = False
                        return success

                elif first_load_response == "File received successfully\n":
                    success = True
                    return success

                elif first_load_response == "crc_error\n":
                    raise socket.timeout

            except socket.timeout as e:
                counter_try += 1
                if counter_try > crc_try:
                    msg = f"    Проблемы с сетью, попробуйте еще раз: {e}"
                    logging.error(msg)
                    self.emit_status(msg, ip)
                    success = False

            except socket.error as e:
                msg = f"    Загрузка файла была прервана, пожалуйста, проверьте подключение к сети и повторите попытку: {e}"
                logging.error(msg)
                self.emit_status(msg, ip)
                success = False
                break

            except Exception as e:
                msg = f"    произошла неизвестная ошибка, повторите попытку: {e}"
                logging.error(msg)
                self.emit_status(msg, ip)
                return False

        if counter_try >= crc_try:
            sock.close()
            return success


    def run(self):
        try:
            logger.info(f"\n____OrangeWorkerTCP run: {self.ip} '{self.command}'")
            self.work(self.ip, 1234)
        except socket.error as e:
            logging.error(f"____OrangeWorkerTCP socket.error: {e}")
            self.emit_status(f"Не достучались до зоны, проверьте сеть! {self.command}", self.ip)
        except Exception as e:
            logging.error(f"____OrangeWorkerTCP Exception: {e}")
        self.final_signal.emit(True)
        return