from PyQt5.QtWidgets import QProgressBar, QGraphicsOpacityEffect


class IndicatorProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 0)  # Делает индикатор бесконечным
        self.stopIndicate()

    def indicate(self):
        self._make_visible(self)

    def stopIndicate(self):
        self._make_invisible(self)

    def _make_invisible(self, widget):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(0)
        widget.setGraphicsEffect(effect)

    def _make_visible(self, widget):
        widget.setGraphicsEffect(None)
