import asyncio
import json
import logging

import aiohttp
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class YandexThread(QThread):
    yandex_things_status = pyqtSignal(str, dict)

    def __init__(self, file_path, file_name, TEXT, TOKEN, folder_id, VOICE, EMOTION):
        super().__init__()
        self.file_path = file_path
        self.file_name = file_name
        self.TEXT = TEXT
        self.TOKEN = TOKEN
        self.FOLDER_ID = folder_id
        self.VOICE = VOICE
        self.EMOTION = EMOTION

        self.create_file_item_params = {
            "success": 1,  # 1 когда успешно, 0 когда не успешно
            "file_path": self.file_path,
            "file_name": self.file_name,
            "text": self.TEXT,
            "voice": f"{self.VOICE[0]}{self.EMOTION[0]}",
        }

    async def get_text_to_speech_file(self):
        logger.info(f"run on thread ya {self.file_path} {self.VOICE}")

        params = {
            "text": self.TEXT,
            "lang": "ru-RU",
            "folderId": self.FOLDER_ID,
            "sampleRateHertz": 48000,
            "speed": 1,
            "voice": self.VOICE,
            "emotion": self.EMOTION,
            "format": "mp3"
        }

        try:
            url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
            headers = {"Authorization": f"Bearer {await self.get_iam(self.TOKEN)}"}
            # headers = {"Authorization": f"Bearer {await self.get_iam('123123')}"}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params, headers=headers) as response:
                    logger.info(f"YA Response status: {response.status}")
                    if response.status == 200:
                        with open(f"{self.file_path}", "wb") as f:
                            f.write(await response.read())

                        self.create_file_item_params["success"] = 1
                        self.yandex_things_status.emit("response", self.create_file_item_params)
                    else:
                        logger.info(f"YA Response text: {await response.text()}")
                        raise Exception

        except Exception as e:
            self.create_file_item_params["success"] = 0
            self.yandex_things_status.emit(f"ошибка: {e}", self.create_file_item_params)
            logger.info(f"____YandexThread run ошибка: {e}")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.get_text_to_speech_file())

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
