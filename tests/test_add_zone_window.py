import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit

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


if __name__ == "__main__":
    unittest.main()
