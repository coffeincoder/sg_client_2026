import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PyQt5.QtWidgets import QApplication, QCheckBox, QLabel

from src.data.ZoneModel import Orange
from src.ui.custom.zone.ZoneListItem import ZoneListItem

app = QApplication.instance() or QApplication([])


class TestZoneListItemSubzoneCheckboxes(unittest.TestCase):
    def test_present_channels_shown_as_checkboxes(self):
        zone = Orange(
            name="zone1",
            ip="1.1.1.1",
            subzone1=True,
            subzone1_present=True,
            subzone1_name="улица",
            subzone2=False,
            subzone2_present=False,
            subzone3=True,
            subzone3_present=True,
            subzone3_name="второй этаж",
            subzone4=False,
            subzone4_present=False,
        )
        item = ZoneListItem(zone)

        labels = item.subzones_container.findChildren(QLabel)
        checkboxes = item.subzones_container.findChildren(QCheckBox)

        self.assertEqual(len(labels), 0)
        self.assertEqual(sorted(c.text() for c in checkboxes), ["второй этаж", "улица"])

    def test_no_present_channels_shows_no_checkboxes(self):
        zone = Orange(name="zone2", ip="1.1.1.2")
        item = ZoneListItem(zone)

        checkboxes = item.subzones_container.findChildren(QCheckBox)
        self.assertEqual(len(checkboxes), 0)


if __name__ == "__main__":
    unittest.main()
