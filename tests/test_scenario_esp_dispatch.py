import unittest

from src.viewmodel.playback_viewmodel import should_send_esp


class TestShouldSendEsp(unittest.TestCase):
    def test_empty_no(self):
        self.assertFalse(should_send_esp(""))
        self.assertFalse(should_send_esp(None))

    def test_nonempty_yes(self):
        self.assertTrue(should_send_esp("evac.mp3"))


if __name__ == "__main__":
    unittest.main()
