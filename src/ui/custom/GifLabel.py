from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QLabel

import paths


class GifLabel(QLabel):
    def __init__(self, movie_path=f'{paths.img_files}{paths.sep}mic.gif'):
        super().__init__()
        self.original_size = self.size()  # Сохраняем исходный размер
        self.movie = QMovie(movie_path)
        self.setMovie(self.movie)
        self.movie.setScaledSize(self.original_size / 8)
        self.movie.start()

    def change_gif(self, path):
        self.movie = QMovie(path)
        self.setMovie(self.movie)
        if path.find("mic.gif") != -1:
            self.movie.setScaledSize(self.original_size / 8)
        else:
            self.movie.setScaledSize(self.original_size / 8)
        self.movie.start()
