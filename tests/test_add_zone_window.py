import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest import mock

from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit, QDialog, QMessageBox

from src.ui.fragments.UI_AddZoneWindow import UI_AddZoneWindow

app = QApplication.instance() or QApplication([])


class TestAddZoneWindowChannels(unittest.TestCase):
    def test_construct_with_channels(self):
        channels = [(True, "a"), (False, "b"), (True, "c"), (False, "d")]
        w = UI_AddZoneWindow("zone", "1.1.1.1", [], channels=channels)

        checks = [ch for ch in w.channel_checks]
        fields = [f for f in w.channel_fields]
        self.assertEqual(len(checks), 4)
        self.assertEqual(len(fields), 4)
        self.assertTrue(all(isinstance(c, QCheckBox) for c in checks))
        self.assertTrue(all(isinstance(f, QLineEdit) for f in fields))

        self.assertTrue(fields[0].isEnabled())
        self.assertFalse(fields[1].isEnabled())

        self.assertEqual(w.get_channels(), channels)

    def test_toggle_checkbox_enables_field(self):
        channels = [(True, "a"), (False, "b"), (True, "c"), (False, "d")]
        w = UI_AddZoneWindow("zone", "1.1.1.1", [], channels=channels)

        w.channel_checks[1].setChecked(True)

        self.assertTrue(w.channel_fields[1].isEnabled())
        self.assertTrue(w.get_channels()[1][0])

    def test_default_channels_none(self):
        w = UI_AddZoneWindow("zone", "1.1.1.1", [], channels=None)

        for chk in w.channel_checks:
            self.assertFalse(chk.isChecked())
        for fld in w.channel_fields:
            self.assertFalse(fld.isEnabled())

        self.assertEqual(w.get_channels(), [(False, ""), (False, ""), (False, ""), (False, "")])

    def test_validate_rejects_zero_channels(self):
        """Should not accept if no channels are active."""
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=None)

        with mock.patch.object(QMessageBox, 'information'):
            w.validate_and_accept()

        self.assertNotEqual(w.result(), QDialog.Accepted)

    def test_validate_accepts_with_at_least_one_channel(self):
        """Should accept if at least one channel is active."""
        channels = [(True, "out1"), (False, ""), (False, ""), (False, "")]
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=channels)

        with mock.patch.object(QMessageBox, 'information'):
            w.validate_and_accept()

        self.assertEqual(w.result(), QDialog.Accepted)


if __name__ == "__main__":
    unittest.main()
