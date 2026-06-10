from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import paths


class AnimatedImage(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(AnimatedImage, self).__init__(*args, **kwargs)
        self._pixmap = QtGui.QPixmap()
        self._animation_in = QtCore.QPropertyAnimation(self, b'geometry')
        self._animation_out = QtCore.QPropertyAnimation(self, b'geometry')
        self._animation_in.setDuration(500)  # Продолжительность анимации увеличения - 0.5 секунды
        self._animation_out.setDuration(500)  # Продолжительность анимации уменьшения - 0.5 секунды
        self._animation_in.finished.connect(self._animation_out.start)
        self._animation_out.finished.connect(self._animation_in.start)
        self.setScaledContents(True)  # Добавлено

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.setPixmap(self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def start_animation(self, duration=None):
        if self._animation_in.state() != QtCore.QAbstractAnimation.Running:
            start_rect = QtCore.QRect(self.pos(), self.size())
            end_rect = QtCore.QRect(
                self.pos() - QtCore.QPoint(round(self.size().width() * 0.05), round(self.size().height() * 0.05)),
                self.size() * 1.1)
            self._animation_in.setStartValue(start_rect)
            self._animation_in.setEndValue(end_rect)
            self._animation_out.setStartValue(end_rect)
            self._animation_out.setEndValue(start_rect)
            self._animation_in.start()
            if duration is not None:
                QtCore.QTimer.singleShot(duration * 1000,
                                         self.stop_animation)  # Остановка анимации после заданного времени

    def stop_animation(self):
        if self._animation_in.state() == QtCore.QAbstractAnimation.Running:
            self._animation_in.stop()
        if self._animation_out.state() == QtCore.QAbstractAnimation.Running:
            self._animation_out.stop()
        self.setPixmap(self._pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                                           Qt.SmoothTransformation))  # Сброс изображения до исходного состояния
