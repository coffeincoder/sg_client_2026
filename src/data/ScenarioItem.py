import json

class ScenarioItem:
    def __init__(self, zone, file, file_esp_filename=None, **kwargs):


        self.zone = zone
        self.file = file
        self.file_esp_filename = file_esp_filename

