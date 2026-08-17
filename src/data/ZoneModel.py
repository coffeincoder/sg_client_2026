from dataclasses import dataclass


@dataclass
class Orange:
    name: str = "default"
    ip: str = "192.168."
    isChecked: bool = False
    is_playing: bool = False
    is_streaming: bool = False
    is_sip_running: bool = False
    is_warning: bool = False
    is_online: bool = False
    tooltip_warn_message: str = ""
    tooltip_message: str = ""
    zone_type: str = ""
    subzone1: bool = False
    subzone2: bool = False
    subzone3: bool = False
    subzone4: bool = False
    subzone1_name: str = ""
    subzone2_name: str = ""
    subzone3_name: str = ""
    subzone4_name: str = ""
    def to_json(self):
        return self.__dict__

