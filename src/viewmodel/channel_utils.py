from src.data.ZoneModel import Orange


def active_channels(zone: Orange) -> list:
    """Номера каналов, которые есть у устройства (present) И активны (1..8)."""
    return [n for n in range(1, 9)
            if getattr(zone, f"subzone{n}") and getattr(zone, f"subzone{n}_present")]


def format_play_variant(channels: list) -> str:
    """Список активных линий в строку протокола: [1,3,4] -> '1,3,4', [] -> ''."""
    return ",".join(str(n) for n in channels)


def resolve_active(was_present: bool, is_present: bool, was_active: bool) -> bool:
    """Правило active при сохранении окна устройства."""
    if not is_present:
        return False
    if not was_present:      # канал впервые стал present
        return True
    return was_active        # был present — активность не трогаем
