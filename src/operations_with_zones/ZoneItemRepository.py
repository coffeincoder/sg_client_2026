import json
import logging
from typing import List, Set, Optional
from dataclasses import asdict
from paths import zones_json
from src.data.ZoneModel import Orange

logger = logging.getLogger(__name__)


class ZoneItemRepository:
    def __init__(self):
        self.all_zones: List[Orange] = []
        self.checked_zones: Set[Orange] = set()
        self.init_load()

    def add_zone(self, zone: Orange):
        """Добавляет новую зону с проверкой на уникальность"""
        if not any(z.name == zone.name for z in self.all_zones):
            self.all_zones.append(zone)
            self._save_all_zones()
            logger.info(f"Добавлена новая зона: {zone.name}")

    def add_zone_from_file(self, file: str):
        """Добавляет зоны из файла с обработкой кодировок"""
        try:
            with open(file, 'r', encoding="UTF-8") as f:
                data = f.read()
                new_zones = json.loads(data)
            logger.info("Файл в кодировке UTF-8")
        except UnicodeError:
            logger.info("Файл в кодировке windows-1251")
            with open(file, 'r') as f:
                data = f.read()
                new_zones = json.loads(data.encode("windows-1251").decode("utf-8"))

        for zone_data in new_zones:
            if not all(key in zone_data for key in ['name', 'ip', 'isChecked']):
                logger.warning(f"Некорректные данные зоны: {zone_data}")
                continue

            # Проверяем существование зоны с таким же именем или IP
            existing_names = {z.name for z in self.all_zones}
            existing_ips = {z.ip for z in self.all_zones}

            if zone_data['ip'] in existing_ips:
                logger.info(f"Зона с IP {zone_data['ip']} уже существует, пропускаем")
                continue

            # Модифицируем имя если оно уже существует
            if zone_data['name'] in existing_names:
                zone_data['name'] += ' (new)'
                logger.info(f"Дубликат имени зоны, переименовано в: {zone_data['name']}")

            new_zone = Orange(
                name=zone_data["name"],
                ip=zone_data["ip"],
                isChecked=zone_data["isChecked"],
                subzone1=zone_data.get("subzone1", False),
                subzone2=zone_data.get("subzone2", False),
                subzone3=zone_data.get("subzone3", False),
                subzone4=zone_data.get("subzone4", False),
                subzone1_name=zone_data.get("subzone1_name", ""),
                subzone2_name=zone_data.get("subzone2_name", ""),
                subzone3_name=zone_data.get("subzone3_name", ""),
                subzone4_name=zone_data.get("subzone4_name", "")
            )
            self.add_zone(new_zone)

    def remove_zone(self, zone: Orange):
        """Удаляет зону из репозитория"""
        if zone in self.all_zones:
            self.all_zones.remove(zone)
            self._save_all_zones()
            logger.info(f"Зона удалена: {zone.name}")

    def get_zone_by_name(self, name: str) -> Optional[Orange]:
        """Возвращает зону по имени или None если не найдена"""
        for zone in self.all_zones:
            if zone.name == name:
                return zone
        return None

    def update_zone(self, updated_zone: Orange):
        """Обновляет данные зоны"""
        for i, zone in enumerate(self.all_zones):
            if zone.name == updated_zone.name:
                self.all_zones[i] = updated_zone
                self._save_all_zones()
                logger.info(f"Зона обновлена: {updated_zone.name}")
                return
        logger.warning(f"Зона для обновления не найдена: {updated_zone.name}")

    def update_zone_state(self, zone_name: str,
                        is_checked: Optional[bool] = None,
                        subzone1: Optional[bool] = None,
                        subzone2: Optional[bool] = None,
                        subzone1_name: Optional[str] = None,
                        subzone2_name: Optional[str] = None,
                        subzone3: Optional[bool] = None,
                        subzone4: Optional[bool] = None,
                        subzone3_name: Optional[str] = None,
                        subzone4_name: Optional[str] = None):
        """
        Обновляет состояние зоны и подзон
        Args:
            zone_name: Имя зоны для обновления
            is_checked: Состояние главного чекбокса
            subzone1: Состояние подзоны 1
            subzone2: Состояние подзоны 2
            subzone1_name: Название подзоны 1
            subzone2_name: Название подзоны 2
            subzone3: Состояние подзоны 3
            subzone4: Состояние подзоны 4
            subzone3_name: Название подзоны 3
            subzone4_name: Название подзоны 4
        """
        zone = self.get_zone_by_name(zone_name)
        if zone:
            if is_checked is not None:
                zone.isChecked = is_checked
            if subzone1 is not None:
                zone.subzone1 = subzone1
            if subzone2 is not None:
                zone.subzone2 = subzone2
            if subzone1_name is not None:
                zone.subzone1_name = subzone1_name
            if subzone2_name is not None:
                zone.subzone2_name = subzone2_name
            if subzone3 is not None:
                zone.subzone3 = subzone3
            if subzone4 is not None:
                zone.subzone4 = subzone4
            if subzone3_name is not None:
                zone.subzone3_name = subzone3_name
            if subzone4_name is not None:
                zone.subzone4_name = subzone4_name
            self._save_all_zones()

    def get_all(self) -> List[Orange]:
        """Возвращает все зоны, загружая их из файла если нужно"""
        if not self.all_zones:
            self.init_load()
        return self.all_zones

    def get_checked(self) -> Set[Orange]:
        """Возвращает множество выбранных зон"""
        self.checked_zones = {zone for zone in self.all_zones if zone.isChecked}
        return self.checked_zones

    def init_load(self):
        """Инициализирует загрузку зон из файла"""
        try:
            with open(zones_json, 'r') as f:
                zones_data = json.load(f)
                self.all_zones = [
                    Orange(
                        name=z.get('name', ''),
                        ip=z.get('ip', ''),
                        isChecked=z.get('isChecked', False),
                        subzone1=z.get('subzone1', False),
                        subzone2=z.get('subzone2', False),
                        subzone3=z.get('subzone3', False),
                        subzone4=z.get('subzone4', False),
                        subzone1_name=z.get('subzone1_name', ''),
                        subzone2_name=z.get('subzone2_name', ''),
                        subzone3_name=z.get('subzone3_name', ''),
                        subzone4_name=z.get('subzone4_name', '')
                    ) for z in zones_data
                ]
            logger.info(f"Загружено {len(self.all_zones)} зон из файла")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Ошибка загрузки зон: {e}")
            self.all_zones = []

    def save(self, zones: Optional[List[Orange]] = None):
        """Публичное сохранение зон в файл.

        Часть вызовов передаёт список явно (rename_zone -> save(ZONE_LIST)).
        В проде ZONE_LIST это тот же объект, что и self.all_zones
        (MainWindow: ZONE_LIST = zones_repo.all_zones), поэтому переприсваивание
        безопасно и не рассинхронизирует ссылку. Если аргумент не передан —
        сохраняем текущее состояние.
        """
        if zones is not None:
            self.all_zones = zones
        self._save_all_zones()

    def _save_all_zones(self):
        """Внутренный метод для сохранения всех зон в файл"""
        try:
            with open(zones_json, 'w') as f:
                json.dump([asdict(zone) for zone in self.all_zones], f, indent=4)
            logger.info("Зоны успешно сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения зон: {e}")