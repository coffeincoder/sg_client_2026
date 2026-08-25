import unittest
from src.viewmodel.channel_utils import resolve_active


class TestResolveActive(unittest.TestCase):
    def test_new_present_becomes_active(self):
        # (was_present, is_present, was_active) -> active
        self.assertTrue(resolve_active(False, True, False))   # впервые отметили
    def test_existing_present_keeps_active(self):
        self.assertFalse(resolve_active(True, True, False))   # был present, active как был
        self.assertTrue(resolve_active(True, True, True))
    def test_unpresent_clears_active(self):
        self.assertFalse(resolve_active(True, False, True))   # сняли present


if __name__ == "__main__":
    unittest.main()
