from PyQt5.QtCore import QObject

from src.viewmodel.files_viewmodel import FilesViewModel
from src.viewmodel.scenarios_viewmodel import ScenariosViewModel


class MainViewModel(QObject):
    """Агрегатор фич-ViewModel'ей. Заполняется по мере переноса фич (Фаза 2)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.files = FilesViewModel(view)
        self.scenarios = ScenariosViewModel(view)
        # фич-VM подключаются здесь в Фазе 2:
        # self.zones = ZonesViewModel(view)
        # ...
