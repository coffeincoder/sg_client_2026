from PyQt5.QtCore import QObject


class MainViewModel(QObject):
    """Агрегатор фич-ViewModel'ей. Заполняется по мере переноса фич (Фаза 2)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # фич-VM подключаются здесь в Фазе 2:
        # self.files = FilesViewModel(view)
        # self.zones = ZonesViewModel(view)
        # ...
