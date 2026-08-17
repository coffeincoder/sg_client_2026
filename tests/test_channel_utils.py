import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestChannelUtils(unittest.TestCase):
    def test_active_channels_mixed(self):
        z = Orange(subzone1=True, subzone2=False, subzone3=True, subzone4=True)
        self.assertEqual(active_channels(z), [1, 3, 4])

    def test_active_channels_none(self):
        z = Orange()
        self.assertEqual(active_channels(z), [])

    def test_format_play_variant(self):
        self.assertEqual(format_play_variant([1, 3, 4]), "1,3,4")
        self.assertEqual(format_play_variant([]), "")


if __name__ == "__main__":
    unittest.main()
