import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.operations_with_zones.ZoneItemRepository import ZoneItemRepository


class TestZoneSaveChannels(unittest.TestCase):
    """Проверяет, что update_zone_state сохраняет каналы 3/4 в zones.json
    без побочного влияния на существующие каналы 1/2 (без off-by-one)."""

    def test_update_zone_state_persists_channels_3_and_4(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zones_path = os.path.join(tmp_dir, "zones.json")
            initial_zones = [
                {
                    "name": "zone-1",
                    "ip": "192.168.1.1",
                    "isChecked": True,
                    "subzone1": False,
                    "subzone2": False,
                    "subzone3": False,
                    "subzone4": True,
                    "subzone1_name": "",
                    "subzone2_name": "",
                    "subzone3_name": "",
                    "subzone4_name": "old",
                }
            ]
            with open(zones_path, "w") as f:
                json.dump(initial_zones, f)

            with patch("src.operations_with_zones.ZoneItemRepository.zones_json", zones_path):
                repo = ZoneItemRepository()
                repo.update_zone_state(
                    "zone-1",
                    subzone3=True,
                    subzone3_name="c",
                    subzone4=False,
                )

            with open(zones_path, "r") as f:
                saved = json.load(f)

        zone = saved[0]
        self.assertIs(zone["subzone3"], True)
        self.assertEqual(zone["subzone3_name"], "c")
        self.assertIs(zone["subzone4"], False)
        # каналы 1/2 не должны были измениться
        self.assertIs(zone["subzone1"], False)
        self.assertIs(zone["subzone2"], False)


if __name__ == "__main__":
    unittest.main()
