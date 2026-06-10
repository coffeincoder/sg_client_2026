import logging
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import socket
import os
import re

logger = logging.getLogger(__name__)

def cut_filename(s):
    first_space_index = s.find('NAME:')
    second_space_index = s.find('mp3', first_space_index + 1)
    if first_space_index != -1 and second_space_index != -1:
        return s[5 + first_space_index + 1:second_space_index + 3]
    else:
        return ''
class ESP32WorkerTCP(QThread):
    started = pyqtSignal(int)
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)


    def __init__(self, IP, PORT, file, vol, loop, command):
        QThread.__init__(self)
        self.IP = IP
        self.PORT = PORT
        self.file = file
        self.command = command
        self.vol = vol
        self.loop = loop

    @pyqtSlot()
    def run(self):  # Используем метод run вместо do_work
        # Выполняем работу

        if self.command == 'play':

            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                client_socket.settimeout(100)
                server_address = (self.IP, self.PORT)
                client_socket.connect(server_address)
            except Exception as e:
                logger.info(e)
                return

            message = 'Ksb-rso15'
            try:
                client_socket.sendall(message.encode())

                data = client_socket.recv(1024)
                logger.info(data.decode())

            except Exception as e:
                logger.info(e)
                return
            # шлем пароль в любом случае

            files_to_del = []

            message = 'dir'
            try:
                client_socket.sendall(message.encode())
                while True:

                    data = client_socket.recv(1024)
                    _file_to_del = data.decode()
                    file_to_del = cut_filename(_file_to_del)
                    if _file_to_del != '':
                        files_to_del.append(file_to_del)
                    if ((data.decode().find('Free bytes') != -1)):
                        break
            except Exception as e:
                logger.info(e)
            logger.info(files_to_del)

            # удаляем все файлы
            for file_to_del in files_to_del:
                if file_to_del != '':
                    message = 'del ' + file_to_del
                    try:
                        client_socket.sendall(message.encode())
                        while True:
                            data = client_socket.recv(64).decode()
                            logger.info(data)
                            if ((data.find('deleted') != -1)):
                                break
                    except Exception as e:
                        logger.info(e)
                        return

            message = 'load ' + self.file  ###################################################################

            logger.info('pr')
            try:
                client_socket.sendall(message.encode())
                logger.info(1)
                while True:
                    data = client_socket.recv(32)
                    logger.info(data.decode())
                    logger.info(data.decode().find('loadready'))
                    logger.info(data.decode().find('password'))

                    if ((data.decode().find('loadready') != - 1) or (data.decode().find('password:') != - 1)):
                        break

            except Exception as e:
                logger.info(e)
                return

            # загрузка файла
            answer = data.decode()
            logger.info('ans')

            logger.info(answer[10:])

            ESP_free_bytes = int(answer[10:])
            logger.info(self.file)
            f = open(self.file, mode='rb')
            size_of_file = os.path.getsize(self.file)
            logger.info(size_of_file)
            last_part = size_of_file % 1400
            logger.info('1111111111111111', size_of_file % 1400)
            message = 'size ' + str(size_of_file + 1400 * 2 + last_part)
            logger.info(size_of_file)
            logger.info(message)
            client_socket.sendall(message.encode())
            while True:
                data = client_socket.recv(64)
                logger.info(data.decode())
                if data.decode().find('loadpart') != -1:
                    break
                logger.info(data.decode()[14:])
            data = ''
            logger.info('OK')
            total_progress = int(size_of_file / 1400)


            count_iter = int(size_of_file / 1400)
            i = 0

            progress_bar_touch = 0
            pr_exit = 0
            # d = f.read(int(1400))
            # client_socket.send(d)
            while (i < count_iter + 4):

                while True:
                    data = client_socket.recv(32).decode()
                    print(data)
                    if (data.find('loadpart') != - 1):
                        break
                    if data.find('successfully') != - 1:
                        pr_exit = 1
                        break
                if pr_exit == 1:
                    break
                part = re.findall(r'\d+', data)[-1]
                print("data", data)
                print("part", part)
                if i > 0:
                    d = f.read(int(part))
                else:
                    d = f.read(1400)
                if i >= count_iter:
                    client_socket.send(b'\\x00' * int(part))
                else:
                    client_socket.send(d)

                progress_bar_touch = progress_bar_touch + 1

                i = i + 1
                print("part=", part)
            client_socket.close()
            sleep(1)
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                client_socket.settimeout(100)
                server_address = (self.IP, self.PORT)
                client_socket.connect(server_address)
            except Exception as e:
                print(e)

            # шлем пароль в любом случае

            message = 'vol ' + self.vol
            try:
                client_socket.sendall(message.encode())
                data = client_socket.recv(32)
                print(data.decode())
            except Exception as e:
                print(e)

            message = 'play 999.mp3'
            try:
                client_socket.sendall(message.encode())
                data = client_socket.recv(1024)
                print(data.decode())
            except Exception as e:
                print(e)
            message = 'loop ' + '1'
            try:
                client_socket.sendall(message.encode())
                data = client_socket.recv(1024)
                print(data.decode())
            except Exception as e:
                print(e)
            message = 'time ' + str(int(self.loop) - 1)
            try:
                client_socket.sendall(message.encode())
                data = client_socket.recv(1024)
                print(data.decode())
            except Exception as e:
                print(e)
            client_socket.close()

            return
        if self.command == 'stop':

            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                client_socket.settimeout(100)
                server_address = (self.IP, self.PORT)
                client_socket.connect(server_address)
            except Exception as e:
                print(e)
                return
            message = 'stop'
            try:
                client_socket.sendall(message.encode())

                data = client_socket.recv(1024)
                print(data.decode())

            except Exception as e:
                print(e)
                return
            client_socket.close()

            return

        # шлем пароль в любом случае
