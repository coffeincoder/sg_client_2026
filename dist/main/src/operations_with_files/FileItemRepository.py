import json
import logging
import os.path
import re
from datetime import datetime
from typing import List

from mutagen.mp3 import MP3

import paths
from src.data.FileModel import FileItem

logger = logging.getLogger(__name__)


class FileItemRepository:
    def __init__(self):
        self.file_list: List[FileItem] = []

    def add_file(self, file_item: FileItem):
        """Нужно условиться что filename это именно имя файла, а не путь к нему или текст"""
        if file_item not in self.file_list:
            self.file_list.insert(0, file_item)
            self.save()
            logger.info(f"FileItemRepository: add_data {len(self.file_list)} {self.file_list}")

    def _get_all(self) -> List[FileItem]:
        self.file_list.clear()
        with open(paths.data_scenaries_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data is not None:
                for file_item in data:
                    new_file = FileItem.from_json(file_item)
                    self.file_list.append(new_file)

        return self.check_if_files_exists(self.file_list)

    def get(self):
        self.file_list = self._get_all()
        return self.file_list

    def sort_list(self, sort_key="create_date", reverse_key=True) -> List[FileItem]:
        logger.info(f'FileItemRepository: sort param {sort_key}')
        logger.info(f'FileItemRepository: reverse {reverse_key}')
        self.file_list = sorted(self.file_list, key=lambda x: getattr(x, sort_key), reverse=reverse_key)
        return self.file_list

    def save(self):
        with open(paths.data_scenaries_json, 'w', encoding='utf-8') as f:
            json.dump([file.to_json() for file in self.file_list], f, ensure_ascii=False, indent=4)

    def remove_file(self, file_item: FileItem):
        if file_item in self.file_list:
            self.file_list.remove(file_item)
        if file_item.filename in os.listdir(paths.mp3_files):
            os.remove(os.path.join(paths.mp3_files, file_item.filename))
        self.save()

    def check_if_files_exists(self, file_list: List[FileItem]) -> List[FileItem]:
        self.remove_trash()

        filtered_list = []
        for file_item in file_list:
            file_path = f"{paths.mp3_files}{paths.sep}{file_item.filename}"
            file_path2 = file_item.filename
            file_path3 = file_item.text
            if os.path.exists(file_path) or os.path.exists(file_path2) or os.path.exists(file_path3):
                filtered_list.append(file_item)

        for filename in os.listdir(paths.mp3_files):
            if not any(file_item.filename == filename for file_item in filtered_list):
                # Если файла нет в self.file_list, добавляем новый объект FileItem
                full_path = find_file(filename, paths.mp3_files)
                try:
                    audio = MP3(full_path)
                    duration = round(audio.info.length)
                except Exception:
                    duration = 0
                create_time = get_creation_date(full_path)
                extracted_fname = extract_filename_from_ya_pattern(filename)

                new_file: FileItem = FileItem(
                    header=extracted_fname[:-4] if extracted_fname else filename[:-4],
                    filename=filename,
                    text=f"Пользовательский файл из {full_path}",
                    duration=duration,
                    create_date=create_time,
                )
                filtered_list.append(new_file)

        self.file_list = filtered_list

        return self.sort_list()

    def remove_trash(self):
        mp3_folder = paths.mp3_files

        if not os.path.exists(mp3_folder):
            os.makedirs(mp3_folder)

        for file in os.listdir(mp3_folder):
            if file[-4:] == ".ogg" or file[-4:] == ".wav":
                os.remove(f"{paths.mp3_files}{os.sep}{file}")


def get_creation_date(path):
    timestamp = os.path.getctime(path)
    date = datetime.fromtimestamp(timestamp)
    return date.strftime("%d.%m.%Y  %H:%M")


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def extract_filename_from_ya_pattern(filename):
    pattern = r'^(fg|fn|an|ag)\d{5}(.*)$'
    match = re.match(pattern, filename)
    if match:
        return match.group(2)
    else:
        return None
