import json
import os
import tempfile
import unittest
from unittest import mock

from src.data.ZoneModel import Orange
import src.operations_with_zones.ZoneItemRepository as repo_mod
from src.operations_with_zones.ZoneItemRepository import ZoneItemRepository


class TestZoneModel8ch(unittest.TestCase):
    def test_new_channels_default(self):
        z = Orange()
        for n in (5, 6, 7, 8):
            self.assertEqual(getattr(z, f"subzone{n}"), False)
            self.assertEqual(getattr(z, f"subzone{n}_name"), "")
        for n in range(1, 9):
            self.assertEqual(getattr(z, f"subzone{n}_present"), False)

    def test_present_fields_serialized(self):
        z = Orange(subzone5=True, subzone5_name="эвакуация", subzone5_present=True)
        d = z.to_json()
        self.assertTrue(d["subzone5"])
        self.assertTrue(d["subzone5_present"])
        self.assertEqual(d["subzone5_name"], "эвакуация")

    def test_migration_present_defaults_through_repository(self):
        """Старый zones.json (2 подзоны, без _present) грузится через РЕАЛЬНЫЙ
        путь ZoneItemRepository.init_load: каналы 1,2 present по умолчанию,
        3..8 нет; существующие поля/имена не теряются. Сторожевой тест на
        совместимость флота (~100 клиентов на старом формате)."""
        old_zones = [{
            "name": "old_zone",
            "ip": "192.168.1.1",
            "isChecked": True,
            "subzone1": True,
            "subzone2": False,
            "subzone1_name": "улица",
            "subzone2_name": "двор",
        }]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "zones.json")
            with open(path, "w") as f:
                json.dump(old_zones, f)
            # init_load читает модульную глобаль zones_json — подменяем её.
            with mock.patch.object(repo_mod, "zones_json", path):
                repo = ZoneItemRepository()

        self.assertEqual(len(repo.all_zones), 1)
        z = repo.all_zones[0]
        # существующие данные не потеряны
        self.assertTrue(z.subzone1)
        self.assertFalse(z.subzone2)
        self.assertEqual(z.subzone1_name, "улица")
        self.assertEqual(z.subzone2_name, "двор")
        # миграция present: 1,2 = True, 3..8 = False
        self.assertTrue(z.subzone1_present)
        self.assertTrue(z.subzone2_present)
        for n in range(3, 9):
            self.assertFalse(getattr(z, f"subzone{n}_present"),
                             f"subzone{n}_present должен быть False у старого файла")


if __name__ == "__main__":
    unittest.main()
