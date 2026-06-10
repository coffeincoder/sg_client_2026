import json
from dataclasses import dataclass


@dataclass
class OrangeLog:
    msg: str = None

    def to_json(self):
        return json.dumps(self.__dict__)