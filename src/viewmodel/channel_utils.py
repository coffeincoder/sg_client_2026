from src.data.ZoneModel import Orange


def active_channels(zone: Orange) -> list:
    """Номера каналов, которые есть у устройства (present) И активны (1..8)."""
    return [n for n in range(1, 9)
            if getattr(zone, f"subzone{n}") and getattr(zone, f"subzone{n}_present")]


def format_play_variant(channels: list) -> str:
    """Список активных линий в строку протокола: [1,3,4] -> '1,3,4', [] -> ''."""
    return ",".join(str(n) for n in channels)
