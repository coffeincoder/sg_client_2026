import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox, QDialog, QStyleFactory
from src.ui.theme import app_stylesheet, tokens_for


def _luminance(color):
    return 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()


class TestDialogThemeContrast(unittest.TestCase):
    """Окна сообщений/диалоги в тёмной теме: светлый текст из `*` должен лежать
    на тёмном фоне. Иначе на Linux/Windows (светлая системная палитра) текст
    невидим — «пустое окно» при ошибке озвучки."""

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        # эмулируем Linux/Windows: Fusion со стандартной (светлой) палитрой
        cls.app.setStyle(QStyleFactory.create("Fusion"))
        cls.app.setPalette(cls.app.style().standardPalette())
        cls.app.setStyleSheet(app_stylesheet("dark"))

    def _bg_luminance(self, widget):
        widget.resize(420, 160)
        image = widget.grab().toImage()
        return _luminance(image.pixelColor(3, 3))

    def _assert_dark_bg(self, widget):
        text_lum = _luminance(QColor(tokens_for("dark").text))
        bg_lum = self._bg_luminance(widget)
        self.assertGreater(text_lum - bg_lum, 100,
                           f"фон диалога слишком светлый для светлого текста: {bg_lum:.0f}")

    def test_message_box_background_is_dark(self):
        box = QMessageBox(QMessageBox.Information, "Не удалось озвучить текст", "текст")
        self._assert_dark_bg(box)

    def test_plain_dialog_background_is_dark(self):
        self._assert_dark_bg(QDialog())


if __name__ == "__main__":
    unittest.main()
