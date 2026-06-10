# src/data/ScenarioModel.py
from dataclasses import field, asdict, dataclass
from typing import List
from src.data.ScenarioItemModel import ScenarioItemModel
import json


@dataclass
class ScenarioModel:
    scenarioName: str
    ScenarioItems: List[ScenarioItemModel] = field(default_factory=list)

    def __str__(self):
        items_str = "\n".join([str(item) for item in self.ScenarioItems])
        return f"Scenario Name: {self.scenarioName}\nScenario Items:\n{items_str}"

    def to_json(self):
        data = asdict(self)
        data["ScenarioItems"] = [item.to_dict() for item in self.ScenarioItems]
        return json.dumps(data, ensure_ascii=False, indent=4)

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        items = [ScenarioItemModel.from_dict(item) for item in data["ScenarioItems"]]
        return cls(scenarioName=data["scenarioName"], ScenarioItems=items)