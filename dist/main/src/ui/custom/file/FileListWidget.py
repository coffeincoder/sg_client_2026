from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget, QVBoxLayout

from src.data.FileModel import FileItem
from src.ui.custom.file.FileListItem import FileListItem
from src.ui.style_sheets import _get_theme


class FileListWidget(QTableWidget):
    """Представление всего списка элементов, по сути контейнер для [FileListItem]"""
    rename_clicked = pyqtSignal(FileItem)
    delete_clicked = pyqtSignal(FileItem)
    listen_clicked = pyqtSignal(FileItem)
    add_description_clicked = pyqtSignal(FileItem)

    def __init__(self, parent=None):
        super(FileListWidget, self).__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def add_file(self, file_item: FileItem, row, col):
        widget = QTableWidgetItem()
        item = FileListItem(file_item, _get_theme())
        item.rename_clicked.connect(lambda: self.rename_file(file_item))
        item.listen_clicked.connect(lambda: self.listen_file(file_item))
        item.delete_clicked.connect(lambda: self.delete_file(file_item))
        item.add_description_clicked.connect(lambda: self.add_description(file_item))

        widget.setSizeHint(item.sizeHint())

        self.setItem(row, col, widget)
        self.setCellWidget(row, col, item)

    def get_selected_file_item_widget(self) -> FileListItem:
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        item = selected_items[0]
        row = item.row()
        column = item.column()
        custom_widget = self.cellWidget(row, column)
        return custom_widget if isinstance(custom_widget, FileListItem) else None

    def update_file_list(self, file_list: List[FileItem], grid_size):
        self.clear()
        rows = len(file_list) // grid_size + (len(file_list) % grid_size > 0)
        self.setRowCount(rows)
        self.setColumnCount(grid_size)

        for index, file_item in enumerate(file_list):
            row = index // grid_size
            col = index % grid_size
            self.add_file(file_item, row=row, col=col)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.resizeRowsToContents()

        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.update()
        self.repaint()

    def rename_file(self, file_item: FileItem):
        self.rename_clicked.emit(file_item)

    def delete_file(self, file_item: FileItem):
        self.delete_clicked.emit(file_item)

    def listen_file(self, file_item: FileItem):
        self.listen_clicked.emit(file_item)

    def add_description(self, file_item: FileItem):
        self.add_description_clicked.emit(file_item)
