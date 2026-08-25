import unittest
from src.data.ZoneModel import Orange
from src.viewmodel.channel_utils import active_channels, format_play_variant


class TestChannelUtils8ch(unittest.TestCase):
    def test_active_requires_present_and_active(self):
        z = Orange(
            subzone1=True, subzone1_present=True,     # активен и есть → входит
            subzone5=True, subzone5_present=False,    # активен, но не present → НЕ входит
            subzone7=True, subzone7_present=True,     # входит
            subzone8=False, subzone8_present=True,    # present, но не активен → нет
        )
        self.assertEqual(active_channels(z), [1, 7])

    def test_format_up_to_8(self):
        self.assertEqual(format_play_variant([1, 5, 7]), "1,5,7")


if __name__ == "__main__":
    unittest.main()
