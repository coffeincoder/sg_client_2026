from src.data.ZoneModel import Orange


def active_channels(zone: Orange) -> list:
    """Номера активных каналов зоны (1..4)."""
    return [n for n in (1, 2, 3, 4) if getattr(zone, f"subzone{n}")]


def format_play_variant(channels: list) -> str:
    """Список активных линий в строку протокола: [1,3,4] -> '1,3,4', [] -> ''."""
    return ",".join(str(n) for n in channels)
