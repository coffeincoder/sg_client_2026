import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from PyQt5 import QtWidgets
from src.ui.root.UI_MainWindow import Ui_MainWindow


class TestMainWindowLayout(unittest.TestCase):
    """Test that add_file_buttons_layout is properly assigned as a self attribute."""

    @classmethod
    def setUpClass(cls):
        """Create QApplication once for all tests."""
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_add_file_buttons_layout_is_instance_attribute(self):
        """Verify that add_file_buttons_layout exists as an instance attribute after setupUi."""
        class _Host(QtWidgets.QMainWindow, Ui_MainWindow):
            pass

        host = _Host()
        host.setupUi(host)

        # Before the fix, this will fail with AttributeError or hasattr will return False
        self.assertTrue(
            hasattr(host, "add_file_buttons_layout"),
            "add_file_buttons_layout not found as instance attribute"
        )
        self.assertIsInstance(
            host.add_file_buttons_layout,
            QtWidgets.QHBoxLayout,
            "add_file_buttons_layout is not a QHBoxLayout"
        )


if __name__ == "__main__":
    unittest.main()
