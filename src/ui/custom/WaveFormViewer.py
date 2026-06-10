import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QProgressBar


class VolumeVisualiser(QProgressBar):
    def __init__(self, parent=None):
        super(VolumeVisualiser, self).__init__(parent)
        self.setRange(0, 30000)
        self.setTextVisible(False)
        self.setMaximumHeight(50)
        self.setInvertedAppearance(True)

    def update_waveform(self, chunk):
        data_int = np.frombuffer(chunk, dtype=np.int16)
        # Вычисление среднего абсолютного значения для получения уровня громкости
        volume_level = np.mean(np.abs(data_int))
        print(int(volume_level))
        # Обновление прогрессбара
        self.setValue(round(volume_level))

