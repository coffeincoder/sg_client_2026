"""
FilesViewModel — логика фичи «Файлы» (список файлов, сортировка, поиск,
    воспроизведение, удаление, переименование, описание, загрузка).

Phase 2, Task 4: методы перенесены из MainWindow VERBATIM.
Виджеты доступны через self.view.<widget>.
Состояние files_repo / FILE_LIST / grid_size оставлено на View
(используется в MainWindow.__init__ ДО создания VM и в не-Files методах).
"""
import logging
import os
import platform
import shlex
import shutil
import subprocess

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog, QDialog

import paths
from paths import mp3_files
from src.data.FileModel import FileItem
from src.operations_with_files.FileItemRepository import get_creation_date
from src.ui.fragments.AddDescriptionDialog import AddDescriptionDialog
from src.ui.fragments.RenameDialog import Rename_Dialog
from src.utils.logger_config import setup_logger

# mutagen MP3 — импортируем как в оригинале (через FileItemRepository star-import)
from mutagen.mp3 import MP3

logger = setup_logger()


class FilesViewModel(QObject):
    """ViewModel для фичи «Файлы». Принимает ссылку на View для доступа к виджетам."""

    def __init__(self, view):
        super().__init__()
        self.view = view

        # Состояние сортировки (только для Files; перенесено из MainWindow)
        self.sort_key = 'create_date'
        self.name_reverse_key = True
        self.date_reverse_key = True

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM (self. → self.view. для
    # виджетов; состояние files_repo/FILE_LIST/grid_size — через self.view)
    # ------------------------------------------------------------------

    def update_list_on_slider(self, val):
        self.view.grid_size = val
        self.update_file_list()
        logger.info(f"main: update_file_list_on_slider: {self.view.grid_size}")
        with open(paths.grid, 'w') as f:
            f.write(str(val))

    def update_file_list(self, new_list=None):
        self.view.progress_indicator.stopIndicate()
        logger.info(f"main: update_file_list: {self.view.FILE_LIST}")

        if new_list:
            self.view.file_list_widget.update_file_list(new_list, self.view.grid_size)
        else:
            self.view.FILE_LIST = self.view.files_repo.file_list
            self.view.file_list_widget.update_file_list(self.view.FILE_LIST, self.view.grid_size)

    def sort_by_name(self):
        self.sort_key = 'header'
        self.name_reverse_key = not self.name_reverse_key
        icon = "sort2.png" if self.name_reverse_key else "sort1.png"
        self.view.sort_by_name_btn.setIcon(QIcon(f"{paths.img_files}/{icon}"))
        self.view.FILE_LIST = self.view.files_repo.sort_list(self.sort_key, self.name_reverse_key)
        self.update_file_list()

    def sort_by_date(self):
        self.sort_key = 'create_date'
        self.date_reverse_key = not self.date_reverse_key
        if self.date_reverse_key:
            self.view.sort_by_date_btn.setIcon(QIcon(f"{paths.img_files}/sort1.png"))
        else:
            self.view.sort_by_date_btn.setIcon(QIcon(f"{paths.img_files}/sort2.png"))

        self.view.FILE_LIST = self.view.files_repo.sort_list(self.sort_key, self.date_reverse_key)
        self.update_file_list()

    def on_search_changed(self, text: str):
        if not text:
            self.view.file_list_widget.update_file_list(self.view.FILE_LIST, self.view.grid_size)
        else:
            q = text.lower()
            filtered = [f for f in self.view.FILE_LIST if q in f.header.lower()]
            self.view.file_list_widget.update_file_list(filtered, self.view.grid_size)

    def play_file_local(self, file_item: FileItem):
        full_path_mp3_folder = os.path.join(os.getcwd(), mp3_files)
        full_path_to_mp3_file = os.path.join(full_path_mp3_folder, file_item.filename)
        logger.info(f"main: play_file_local {full_path_to_mp3_file}")

        if platform.system() == 'Windows':
            command = f"start wmplayer \"{full_path_to_mp3_file}\""
            os.system(command)
        else:
            # Экранируем специальные символы в имени файла
            escaped_path = shlex.quote(full_path_to_mp3_file)
            # Запускаем в фоновом режиме с помощью nohup и &
            command = f'nohup mplayer {escaped_path} > /dev/null 2>&1 &'
            subprocess.Popen(command, shell=True, close_fds=True)

    def delete_file(self, file_item: FileItem):

        logger.info(f"main: delete_file: {file_item}")
        self.view.FILE_LIST.remove(file_item)
        self.view.files_repo.remove_file(file_item)
        self.update_file_list(self.view.FILE_LIST)

    def rename_file(self, file_item: FileItem):
        for file in self.view.FILE_LIST:
            if file_item.filename == file.filename:
                dialog = Rename_Dialog(file_item.header)
                if dialog.exec() == QDialog.Accepted:
                    file.header = dialog.get_text()
                    self.view.files_repo.save()

        self.update_file_list()

    def add_description_to_file_item(self, file_item: FileItem):
        for file in self.view.FILE_LIST:
            if file_item == file:
                dialog = AddDescriptionDialog(file_item)
                if dialog.exec() == QDialog.Accepted:
                    file.text = dialog.get_text()
                    self.view.files_repo.save()
                self.update_file_list()

    def add_file_item(self, header, filename, text, current_voice):

        full_path_mp3_folder = os.path.join(os.getcwd(), mp3_files)
        full_path_to_mp3_file = os.path.join(full_path_mp3_folder, filename)
        audio = MP3(full_path_to_mp3_file)
        duration = audio.info.length
        create_time = get_creation_date(full_path_to_mp3_file)

        self.view.files_repo.add_file(
            FileItem(
                header=header,
                filename=filename,
                text=text,
                duration=round(duration),
                create_date=create_time,
                current_voice=current_voice
            )
        )

        self.update_file_list()

    def upload_custom_file(self):
        options = QFileDialog.Options()
        # options = QFileDialog.DontUseNativeDialog  # Не использовать нативный диалог на macOS

        if platform.system() == 'Windows':
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            download_dir = os.path.join(os.path.expanduser("~"), "Загрузки")

        # Отображение диалогового окна для выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Выбрать файл", download_dir,
                                                   "MP3 files (*.mp3);",
                                                   options=options)
        if file_path:
            logger.info("upload_custom_file: Выбранный файл:", file_path)
            new_file_path = os.path.join(paths.mp3_files, os.path.basename(file_path))
            shutil.copy(file_path, new_file_path)
            audio = MP3(new_file_path)
            length = audio.info.length
            create_time = get_creation_date(new_file_path)
            new_file_item = FileItem(
                header=os.path.basename(new_file_path),
                filename=os.path.basename(new_file_path),
                text=f"Пользовательский файл из {file_path}",
                duration=round(length),
                create_date=create_time,
            )
            self.view.files_repo.add_file(new_file_item)
            # self.FILE_LIST.insert(0, new_file_item)
        self.update_file_list()

    def get_file_item_file_name(self) -> str:
        try:
            widget = self.view.file_list_widget.get_selected_file_item_widget()
            widget_file_name = widget.file_item.filename
            logger.info(widget_file_name)
            return widget_file_name
        except Exception as e:
            logger.info(e)
