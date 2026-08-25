import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest import mock

from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit, QDialog, QMessageBox

from src.ui.fragments.UI_AddZoneWindow import UI_AddZoneWindow

app = QApplication.instance() or QApplication([])


class TestAddZoneWindowChannels(unittest.TestCase):
    def test_construct_with_channels(self):
        channels = [(True, "a"), (False, "b"), (True, "c"), (False, "d"),
                    (True, "e"), (False, "f"), (True, "g"), (False, "h")]
        w = UI_AddZoneWindow("zone", "1.1.1.1", [], channels=channels)

        checks = [ch for ch in w.channel_checks]
        fields = [f for f in w.channel_fields]
        self.assertEqual(len(checks), 8)
        self.assertEqual(len(fields), 8)
        self.assertTrue(all(isinstance(c, QCheckBox) for c in checks))
        self.assertTrue(all(isinstance(f, QLineEdit) for f in fields))

        for i, (present, _) in enumerate(channels):
            self.assertEqual(fields[i].isEnabled(), present)

        self.assertEqual(w.get_channels(), channels)

    def test_toggle_checkbox_enables_field(self):
        channels = [(True, "a"), (False, "b"), (True, "c"), (False, "d"),
                    (True, "e"), (False, "f"), (True, "g"), (False, "h")]
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

        self.assertEqual(w.get_channels(), [(False, "")] * 8)

    def test_validate_rejects_zero_channels(self):
        """Should not accept if no channel is marked present on the device."""
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=None)

        with mock.patch.object(QMessageBox, 'information') as info:
            w.validate_and_accept()

        self.assertNotEqual(w.result(), QDialog.Accepted)
        # New two-level wording: validation is about present channels.
        self.assertIn('у устройства', info.call_args[0][2])

    def test_validate_accepts_with_at_least_one_channel(self):
        """Should accept if at least one channel is active."""
        channels = [(True, "out1"), (False, ""), (False, ""), (False, ""),
                    (False, ""), (False, ""), (False, ""), (False, "")]
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=channels)

        with mock.patch.object(QMessageBox, 'information'):
            w.validate_and_accept()

        self.assertEqual(w.result(), QDialog.Accepted)

    def test_rename_also_requires_one_present_channel(self):
        """Rename path must NOT bypass the min-1-present invariant: an operator
        editing a device cannot save it with every channel unchecked (which
        would silently leave the device with no channels to broadcast to)."""
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=None,
                             for_rename=True)

        with mock.patch.object(QMessageBox, 'information') as info:
            w.validate_and_accept()

        self.assertNotEqual(w.result(), QDialog.Accepted)
        self.assertIn('у устройства', info.call_args[0][2])

    def test_rename_accepts_with_one_present_channel(self):
        """Rename with at least one present channel is accepted."""
        channels = [(True, "out1"), (False, ""), (False, ""), (False, ""),
                    (False, ""), (False, ""), (False, ""), (False, "")]
        w = UI_AddZoneWindow("test_zone", "1.1.1.1", [], channels=channels,
                             for_rename=True)

        with mock.patch.object(QMessageBox, 'information'):
            w.validate_and_accept()

        self.assertEqual(w.result(), QDialog.Accepted)


if __name__ == "__main__":
    unittest.main()
