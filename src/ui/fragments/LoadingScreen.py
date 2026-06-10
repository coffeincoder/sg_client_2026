import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout

from paths import img_files


class LoadingScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        # self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)

        # Создаем QLabel для иконки
        self.icon_label = QLabel()
        self.icon_label.setPixmap(
            QPixmap(os.path.join(img_files, "logo (2).png")))

        # Создаем QLabel для текста
        self.text_label = QLabel("Подключение...")
        self.text_label.setAlignment(Qt.AlignHCenter)

        # Создаем QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Это создаст анимированный прогрессбар

        # Добавляем иконку, текст и прогрессбар в layout
        layout = QVBoxLayout()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        # layout.addWidget(self.progress_bar)
        self.setLayout(layout)
