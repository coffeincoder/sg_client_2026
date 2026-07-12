"""
Pure helper functions extracted from main.py.
No side effects, no Qt, no network — safe to import early.
"""
import json
import re

import pyaudio
from datetime import datetime

import paths
from src.utils.logger_config import setup_logger

logger = setup_logger()


def last_five_chars_of_datetime_timestamp():
    current_timestamp = datetime.now().timestamp()
    timestamp_str = str(current_timestamp)
    return timestamp_str[-5:]


def convert_seconds(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def sanitize_filename(text):
    # Удаление недопустимых символов для имени файла в Windows
    new_text = re.sub(r'[<>":/|?*\n\',\\.]', '', text)

    # Замена пробелов и символа точки на нижнее подчеркивание
    new_text = re.sub(r'[ .]', '_', text)[:70]
    new_text = new_text.replace(':', '')
    new_text = "".join(ch for ch in new_text if ch.isalnum())
    return new_text


def cut_filename(s):
    first_space_index = s.find('NAME:')
    second_space_index = s.find('mp3', first_space_index + 1)
    if first_space_index != -1 and second_space_index != -1:
        return s[5 + first_space_index + 1:second_space_index + 3]
    else:
        return ''


def settings() -> dict:
    with open(paths.settings) as s:
        return json.load(s)


def mic_is_ready():
    p = pyaudio.PyAudio()
    try:
        default_device_index = p.get_default_input_device_info()['index']
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        frames_per_buffer=1024,
                        input=True,
                        input_device_index=default_device_index
                        )
        stream.close()
        return True
    except Exception as e:
        logger.info(f"Ошибка: {e}")
        return False


def set_light_theme():
    with open(paths.settings, 'r') as s:
        settings_dict = json.load(s)
    settings_dict["theme"] = "light"
    with open(paths.settings, 'w') as s:
        json.dump(settings_dict, s)


def set_dark_theme():
    with open(paths.settings, 'r') as s:
        settings_dict = json.load(s)
    settings_dict["theme"] = "dark"
    with open(paths.settings, 'w') as s:
        json.dump(settings_dict, s)
