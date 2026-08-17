import unittest
from src.data.ZoneModel import Orange


class TestZoneModelChannels(unittest.TestCase):
    def test_new_channels_default_off(self):
        z = Orange()
        self.assertEqual(z.subzone3, False)
        self.assertEqual(z.subzone4, False)
        self.assertEqual(z.subzone3_name, "")
        self.assertEqual(z.subzone4_name, "")

    def test_to_json_includes_new_channels(self):
        z = Orange(subzone3=True, subzone3_name="улица")
        d = z.to_json()
        self.assertTrue(d["subzone3"])
        self.assertEqual(d["subzone3_name"], "улица")


if __name__ == "__main__":
    unittest.main()
