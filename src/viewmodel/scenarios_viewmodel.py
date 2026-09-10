"""
ScenariosViewModel — логика фичи «Сценарии» (загрузка, планировщик, watchdog).

Phase 2, Task 5: методы перенесены из MainWindow VERBATIM.
Scheduler/Observer/FileChangeHandler остаются на View (используются в
closeEvent/cleanup); внутри VM доступ идёт через self.view.sheduler и т.д.
"""
import asyncio
import json
from time import sleep

from PyQt5.QtCore import QObject

import paths
from src.data.FileModel import FileItem
from src.data.ScenarioItem import ScenarioItem
from src.data.ScenarioModel import ScenarioModel
from src.data.ZoneModel import Orange
from src.utils.logger_config import setup_logger

logger = setup_logger()


class ScenariosViewModel(QObject):
    """ViewModel для фичи «Сценарии». Принимает ссылку на View для доступа
    к виджетам и объектам Scheduler/Observer (остаются на View)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        # NOTE: self.view.sheduler / self.view.observer создаются ПОЗЖЕ в
        # MainWindow.__init__ — не обращаться к ним здесь, только в методах.

    # ------------------------------------------------------------------
    # Методы перенесены из MainWindow VERBATIM (self.sheduler → self.view.sheduler)
    # ------------------------------------------------------------------

    def on_task_executed(self, s_name, filename):
        # Создание окна сообщения

        sleep(1)
        #scenario_name = self.layout_manager.main_window.scenario_listwidget.currentItem().text()
        print(s_name)
        print('11111111111111111111111111111111111111')
        asyncio.run(self.view.orange_play_scenario(scenario_name=s_name))
        print('22222222222222222222222222222222222222')
        sleep(1)
        # Отображение окна сообщения

    def load_scenarios(self):
        try:
            with open(paths.scenario, 'r', encoding='utf-8') as f:
                all_scenarios = json.load(f)
        except FileNotFoundError:
            return {}

        scenarios = {}

        for scenario_name, scenario_data in all_scenarios.items():
            scenario_items = []

            for item in scenario_data["ScenarioItems"]:
                # Восстанавливаем объект Orange (зону)
                zone_data = item.get("zone_data")
                zone_obj = Orange(**zone_data) if zone_data else None

                # Восстанавливаем объект FileItem (файл)
                file_data = item.get("file_data")
                file_obj = FileItem.from_json(file_data) if file_data else None
                esp_filename = (file_data or {}).get("filename_esp")

                # Создаем объект сценария (предполагается, что у вас есть соответствующий класс)
                scenario_item = ScenarioItem(
                    zone=zone_obj,
                    file=file_obj,
                    file_esp_filename=esp_filename,
                )

                scenario_items.append(scenario_item)

            # Создаем объект ScenarioModel (или другой соответствующий класс)
            scenario = ScenarioModel(
                scenarioName=scenario_name,
                ScenarioItems=scenario_items
            )

            scenarios[scenario_name] = scenario

        return scenarios
