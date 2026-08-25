import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import mock_open, patch

from PyQt5.QtWidgets import QApplication

from src.data.ZoneModel import Orange
from src.ui.custom.zone.ZoneListItem import ZoneListItem

app = QApplication.instance() or QApplication([])


class TestZoneListItemPresentChannelCheckboxes(unittest.TestCase):
    def _make_zone(self):
        return Orange(
            name="z",
            ip="1.1.1.1",
            subzone1_present=True,
            subzone1=True,
            subzone1_name="улица",
            subzone5_present=True,
            subzone5=False,
            subzone5_name="склад",
        )

    def test_only_present_channels_get_checkboxes(self):
        zone = self._make_zone()
        item = ZoneListItem(zone)

        self.assertEqual(set(item.channel_checks.keys()), {1, 5})
        self.assertEqual(item.channel_checks[1].text(), "улица")
        self.assertEqual(item.channel_checks[5].text(), "склад")
        self.assertTrue(item.channel_checks[1].isChecked())
        self.assertFalse(item.channel_checks[5].isChecked())
        for n in (2, 3, 4, 6, 7, 8):
            self.assertNotIn(n, item.channel_checks)

    def test_toggle_checkbox_updates_zone_channel(self):
        zone = self._make_zone()
        item = ZoneListItem(zone)

        # save_zone_state opens zones_json; the toggle handler sets the
        # attribute on self.zone before attempting to save, so we patch
        # builtins.open to keep this test independent of the real
        # zones.json file on disk (the write itself is not under test here).
        with patch("builtins.open", mock_open(read_data="[]")):
            item.channel_checks[1].setChecked(False)

        self.assertIs(item.zone.subzone1, False)

    def test_active_but_not_present_is_hidden(self):
        # Core of the two-level model: a channel that is active in the data
        # but NOT present on the device must NOT appear. This proves the
        # panel filters by present, not by active.
        zone = Orange(
            name="z",
            ip="1.1.1.1",
            subzone1_present=True,
            subzone1=True,
            subzone1_name="улица",
            subzone3_present=False,   # not present...
            subzone3=True,            # ...even though marked active in data
            subzone3_name="призрак",
        )
        item = ZoneListItem(zone)

        self.assertEqual(set(item.channel_checks.keys()), {1})
        self.assertNotIn(3, item.channel_checks)


if __name__ == "__main__":
    unittest.main()
