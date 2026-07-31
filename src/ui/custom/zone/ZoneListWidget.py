import logging
from typing import List

from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from typing_extensions import Optional

from src.data.ZoneModel import Orange
from src.ui.custom.zone.ZoneListItem import ZoneListItem


logger = logging.getLogger(__name__)

class ZoneListWidget(QListWidget):
    delete_clicked = pyqtSignal(Orange)
    rename_clicked = pyqtSignal(Orange)

    def __init__(self, parent=None):
        super(ZoneListWidget, self).__init__(parent)
        self.setSpacing(12)
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")
        # карточки зон должны занимать ширину панели, а не свою предпочтительную,
        # иначе они вылезают вправо и появляется горизонтальный скролл
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def add_zone(self, zone: Orange):
        item = QListWidgetItem()
        zone_widget = ZoneListItem(zone)
        zone_widget.delete_clicked.connect(self.delete_zone)
        zone_widget.rename_clicked.connect(self.rename_zone)

        # ширину не навязываем (0) — элемент возьмёт ширину списка; фиксируем только высоту
        item.setSizeHint(QSize(0, zone_widget.sizeHint().height()))
        self.addItem(item)
        self.setItemWidget(item, zone_widget)

    def update_zones(self, zones: List[Orange]):
        self.clear()
        logger.info("Updating zones list")
        for zone in zones:
            self.add_zone(zone)
    ##
    def get_current_zone(self) -> Optional[Orange]:
        current_item = self.currentItem()
        if current_item:
            zone_widget = self.itemWidget(current_item)
            if zone_widget:
                return zone_widget.zone
        return None

    def rename_zone(self, zone: Orange):
        logger.info(f"Rename zone requested: {zone.name}")
        self.rename_clicked.emit(zone)

    def delete_zone(self, zone: Orange):
        logger.info(f"Delete zone requested: {zone.name}")
        self.delete_clicked.emit(zone)