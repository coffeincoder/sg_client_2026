import asyncio
import json
import logging

import aiohttp
import ffmpeg
import requests
import threading

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class Recognizer(QThread):
    result_signal = pyqtSignal(dict, str)

    def __init__(self, iam_token, folder_id, input_file_path, output_file_path):
        super().__init__()
        self.iam_token = iam_token
        self.folder_id = folder_id
        self.input_file_path = input_file_path  # ~wav
        self.output_file_path = output_file_path  # ogg

    async def transcribe_audio(self):

        """Конвертируем в ogg перед отправкой в распознаватель"""
        ffmpeg.input(self.input_file_path).output(self.output_file_path, audio_bitrate='64k').overwrite_output().run()
        with open(self.output_file_path, "rb") as f:
            data = f.read()  # ogg

        params = {
            "topic": "general",
            "folderId": self.folder_id,
            "lang": "ru-RU"
        }
        try:

            url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
            headers = {"Authorization": f"Bearer {await self.get_iam(self.iam_token)}"}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, params=params) as resp:
                    logger.info(f"YA recognizer Response status: {resp.status}")
                    if resp.status == 200:
                        result = await resp.json()

                        self.result_signal.emit(result, self.output_file_path)

                    else:
                        logger.info(f"YA recognizer Response text: {await resp.text()}")
                        raise Exception

        except Exception as e:
            self.result_signal.emit({"result": ""}, self.output_file_path)
            logger.info(f"____Recognizer run ошибка: {e}")

    # Переопределение метода run
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.transcribe_audio())

    @staticmethod
    async def get_iam(token):
        url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        data = {"yandexPassportOauthToken": token}
        headers = {"Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), headers=headers) as response:
                iam_token = (await response.json()).get("iamToken")
                logger.info(iam_token)
                return iam_token
# Использование класса
