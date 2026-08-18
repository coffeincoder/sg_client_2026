import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PyQt5.QtWidgets import QApplication, QCheckBox, QLabel

from src.data.ZoneModel import Orange
from src.ui.custom.zone.ZoneListItem import ZoneListItem

app = QApplication.instance() or QApplication([])


class TestZoneListItemSubzoneLabels(unittest.TestCase):
    def test_active_channels_shown_as_labels(self):
        zone = Orange(
            name="zone1",
            ip="1.1.1.1",
            subzone1=True,
            subzone1_name="улица",
            subzone2=False,
            subzone3=True,
            subzone3_name="второй этаж",
            subzone4=False,
        )
        item = ZoneListItem(zone)

        labels = item.subzones_container.findChildren(QLabel)
        checkboxes = item.subzones_container.findChildren(QCheckBox)

        self.assertEqual([l.text() for l in labels], ["улица", "второй этаж"])
        self.assertEqual(len(checkboxes), 0)

    def test_no_active_channels_shows_no_labels(self):
        zone = Orange(name="zone2", ip="1.1.1.2")
        item = ZoneListItem(zone)

        labels = item.subzones_container.findChildren(QLabel)
        self.assertEqual(len(labels), 0)


if __name__ == "__main__":
    unittest.main()
