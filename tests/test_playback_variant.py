import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestPlaybackVariant(unittest.TestCase):
    def test_variant_string_from_zone(self):
        z = Orange(subzone1=True, subzone1_present=True,
                   subzone2=False, subzone2_present=True,
                   subzone3=True, subzone3_present=True,
                   subzone4=False, subzone4_present=True)
        value = format_play_variant(active_channels(z))
        self.assertEqual(value, "1,3")

    def test_variant_empty_when_no_channels(self):
        z = Orange()
        self.assertEqual(format_play_variant(active_channels(z)), "")


if __name__ == "__main__":
    unittest.main()
