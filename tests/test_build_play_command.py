import unittest
from src.network.OrangeWorkerTCP import build_play_command


class TestBuildPlayCommand(unittest.TestCase):
    def test_default_mode_is_file(self):
        self.assertEqual(
            build_play_command("a.wav"),
            {"command": "play", "filename": "a.wav", "mode": "file"},
        )

    def test_scenario_mode(self):
        self.assertEqual(
            build_play_command("a.wav", "scenario"),
            {"command": "play", "filename": "a.wav", "mode": "scenario"},
        )

    def test_worker_stores_mode(self):
        from src.network.OrangeWorkerTCP import OrangeWorkerTCP
        w = OrangeWorkerTCP(command="play", ip="1.1.1.1", text="", mode="scenario")
        self.assertEqual(w.mode, "scenario")

    def test_worker_default_mode(self):
        from src.network.OrangeWorkerTCP import OrangeWorkerTCP
        w = OrangeWorkerTCP(command="play", ip="1.1.1.1", text="")
        self.assertEqual(w.mode, "file")


if __name__ == "__main__":
    unittest.main()
