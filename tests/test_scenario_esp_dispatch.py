import unittest

from src.viewmodel.playback_viewmodel import should_send_esp, should_send_orange


class TestShouldSendEsp(unittest.TestCase):
    def test_empty_no(self):
        self.assertFalse(should_send_esp(""))
        self.assertFalse(should_send_esp(None))

    def test_nonempty_yes(self):
        self.assertTrue(should_send_esp("evac.mp3"))


class TestShouldSendOrange(unittest.TestCase):
    def test_orange_none_no(self):
        self.assertFalse(should_send_orange(None))

    def test_orange_empty_filename_no(self):
        class F: filename = ""
        self.assertFalse(should_send_orange(F()))

    def test_orange_valid_yes(self):
        class F: filename = "a.wav"
        self.assertTrue(should_send_orange(F()))


if __name__ == "__main__":
    unittest.main()
