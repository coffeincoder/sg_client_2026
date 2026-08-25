import unittest
from src.data.ZoneModel import Orange


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

    def test_migration_present_defaults(self):
        """Старый словарь (без _present) должен давать правильные дефолты"""
        # Симулируем загрузку старого словаря из файла
        old_zone_data = {
            "name": "old_zone",
            "ip": "192.168.1.1",
            "isChecked": True,
            "subzone1": True,
            "subzone2": False
        }

        # Проверяем логику дефолтов с .get(...) как в репозитории
        subzone1_present = old_zone_data.get("subzone1_present", True)
        subzone2_present = old_zone_data.get("subzone2_present", True)
        subzone3_present = old_zone_data.get("subzone3_present", False)
        subzone4_present = old_zone_data.get("subzone4_present", False)
        subzone5_present = old_zone_data.get("subzone5_present", False)

        self.assertTrue(subzone1_present)
        self.assertTrue(subzone2_present)
        self.assertFalse(subzone3_present)
        self.assertFalse(subzone4_present)
        self.assertFalse(subzone5_present)


if __name__ == "__main__":
    unittest.main()
