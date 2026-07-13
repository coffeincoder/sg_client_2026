from PyQt5.QtCore import QObject

from src.viewmodel.files_viewmodel import FilesViewModel
from src.viewmodel.playback_viewmodel import PlaybackViewModel
from src.viewmodel.recording_viewmodel import RecordingViewModel
from src.viewmodel.scenarios_viewmodel import ScenariosViewModel
from src.viewmodel.tts_viewmodel import TtsViewModel
from src.viewmodel.zones_viewmodel import ZonesViewModel


class MainViewModel(QObject):
    """Агрегатор фич-ViewModel'ей. Заполняется по мере переноса фич (Фаза 2)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.files = FilesViewModel(view)
        self.scenarios = ScenariosViewModel(view)
        self.zones = ZonesViewModel(view)
        self.tts = TtsViewModel(view)
        self.recording = RecordingViewModel(view)
        self.playback = PlaybackViewModel(view)
