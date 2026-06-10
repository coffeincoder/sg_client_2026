import json
import time
from dataclasses import dataclass


@dataclass
class OrangeStatus:
    orange_ip: str
    orange_unique_name: str = ""
    orange_unique_id: int = 0
    is_playing: bool = False
    message: str = ""
    warn_message: str = ""
    current_file: str = ""
    volume_value: int = 100
    start_time: int = 0
    remaining_time: int = 0
    user_priority: int = 0
    is_streaming: bool = False
    is_sip_running: bool = False

    def to_json(self):
        return self.__dict__
