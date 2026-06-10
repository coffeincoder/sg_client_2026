import json
import logging
import sys
import time

logger = logging.getLogger(__name__)

"""
пока думаю сделать отправку на сервер так: парсить существующий лог в [LOG_FILE] и его контент 
отправлять в json формате где заголовком будет id этого клиентского приложения и может еще какая-то информация
"""


class LogManager:
    def __init__(self):
        self.logs = []

    def add_log(self, message, level=logging.INFO):
        # self.logs.append({message})
        logging.log(level, message)

    def save_logs_to_file(self):
        logger.info("save_logs_to_file emulated")
        # with open('logs.json', 'w') as file:
        #     json.dump(self.logs, file, indent=4)
        pass

    def send_logs_to_server(self, server_url):
        logs_to_send = self.logs
        self.logs = []
        # Логика отправки на сервер
        for log in logs_to_send:
            logger.info(f'Sending logs to server: {log}')
        # TODO: Реализовать отправку на сервер
