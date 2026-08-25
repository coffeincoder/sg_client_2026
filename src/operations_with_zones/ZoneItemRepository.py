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
                subzone5=zone_data.get("subzone5", False),
                subzone6=zone_data.get("subzone6", False),
                subzone7=zone_data.get("subzone7", False),
                subzone8=zone_data.get("subzone8", False),
                subzone1_name=zone_data.get("subzone1_name", ""),
                subzone2_name=zone_data.get("subzone2_name", ""),
                subzone3_name=zone_data.get("subzone3_name", ""),
                subzone4_name=zone_data.get("subzone4_name", ""),
                subzone5_name=zone_data.get("subzone5_name", ""),
                subzone6_name=zone_data.get("subzone6_name", ""),
                subzone7_name=zone_data.get("subzone7_name", ""),
                subzone8_name=zone_data.get("subzone8_name", ""),
                subzone1_present=zone_data.get("subzone1_present", True),
                subzone2_present=zone_data.get("subzone2_present", True),
                subzone3_present=zone_data.get("subzone3_present", False),
                subzone4_present=zone_data.get("subzone4_present", False),
                subzone5_present=zone_data.get("subzone5_present", False),
                subzone6_present=zone_data.get("subzone6_present", False),
                subzone7_present=zone_data.get("subzone7_present", False),
                subzone8_present=zone_data.get("subzone8_present", False)
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
                        subzone4_name: Optional[str] = None,
                        subzone5: Optional[bool] = None,
                        subzone6: Optional[bool] = None,
                        subzone7: Optional[bool] = None,
                        subzone8: Optional[bool] = None,
                        subzone5_name: Optional[str] = None,
                        subzone6_name: Optional[str] = None,
                        subzone7_name: Optional[str] = None,
                        subzone8_name: Optional[str] = None,
                        subzone1_present: Optional[bool] = None,
                        subzone2_present: Optional[bool] = None,
                        subzone3_present: Optional[bool] = None,
                        subzone4_present: Optional[bool] = None,
                        subzone5_present: Optional[bool] = None,
                        subzone6_present: Optional[bool] = None,
                        subzone7_present: Optional[bool] = None,
                        subzone8_present: Optional[bool] = None):
        """
        Обновляет состояние зоны и подзон (1..8: active/name/present)
        Args:
            zone_name: Имя зоны для обновления
            is_checked: Состояние главного чекбокса
            subzone1..8: Состояние подзоны (active)
            subzone1_name..8_name: Название подзоны
            subzone1_present..8_present: Есть ли канал у устройства
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
            if subzone5 is not None:
                zone.subzone5 = subzone5
            if subzone6 is not None:
                zone.subzone6 = subzone6
            if subzone7 is not None:
                zone.subzone7 = subzone7
            if subzone8 is not None:
                zone.subzone8 = subzone8
            if subzone5_name is not None:
                zone.subzone5_name = subzone5_name
            if subzone6_name is not None:
                zone.subzone6_name = subzone6_name
            if subzone7_name is not None:
                zone.subzone7_name = subzone7_name
            if subzone8_name is not None:
                zone.subzone8_name = subzone8_name
            if subzone1_present is not None:
                zone.subzone1_present = subzone1_present
            if subzone2_present is not None:
                zone.subzone2_present = subzone2_present
            if subzone3_present is not None:
                zone.subzone3_present = subzone3_present
            if subzone4_present is not None:
                zone.subzone4_present = subzone4_present
            if subzone5_present is not None:
                zone.subzone5_present = subzone5_present
            if subzone6_present is not None:
                zone.subzone6_present = subzone6_present
            if subzone7_present is not None:
                zone.subzone7_present = subzone7_present
            if subzone8_present is not None:
                zone.subzone8_present = subzone8_present
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
                        subzone5=z.get('subzone5', False),
                        subzone6=z.get('subzone6', False),
                        subzone7=z.get('subzone7', False),
                        subzone8=z.get('subzone8', False),
                        subzone1_name=z.get('subzone1_name', ''),
                        subzone2_name=z.get('subzone2_name', ''),
                        subzone3_name=z.get('subzone3_name', ''),
                        subzone4_name=z.get('subzone4_name', ''),
                        subzone5_name=z.get('subzone5_name', ''),
                        subzone6_name=z.get('subzone6_name', ''),
                        subzone7_name=z.get('subzone7_name', ''),
                        subzone8_name=z.get('subzone8_name', ''),
                        subzone1_present=z.get('subzone1_present', True),
                        subzone2_present=z.get('subzone2_present', True),
                        subzone3_present=z.get('subzone3_present', False),
                        subzone4_present=z.get('subzone4_present', False),
                        subzone5_present=z.get('subzone5_present', False),
                        subzone6_present=z.get('subzone6_present', False),
                        subzone7_present=z.get('subzone7_present', False),
                        subzone8_present=z.get('subzone8_present', False)
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