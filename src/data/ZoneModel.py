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
    subzone5: bool = False
    subzone6: bool = False
    subzone7: bool = False
    subzone8: bool = False
    subzone1_name: str = ""
    subzone2_name: str = ""
    subzone3_name: str = ""
    subzone4_name: str = ""
    subzone5_name: str = ""
    subzone6_name: str = ""
    subzone7_name: str = ""
    subzone8_name: str = ""
    subzone1_present: bool = False
    subzone2_present: bool = False
    subzone3_present: bool = False
    subzone4_present: bool = False
    subzone5_present: bool = False
    subzone6_present: bool = False
    subzone7_present: bool = False
    subzone8_present: bool = False
    def to_json(self):
        return self.__dict__

