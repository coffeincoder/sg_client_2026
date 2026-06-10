# src/data/ScenarioItemModel.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioItemModel:
    zone: str
    file: str
    file_esp: str = ""  # Может быть пустым

    def __str__(self):
        return f"{self.zone}: {self.file} | ESP: {self.file_esp}"

    def to_dict(self):
        return {
            "zone": self.zone,
            "file": self.file,
            "file_esp": self.file_esp
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            zone=data.get("zone", ""),
            file=data.get("file", ""),
            file_esp=data.get("file_esp", "")
        )