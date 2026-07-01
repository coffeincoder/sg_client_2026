"""
preview_ui.py — minimal UI preview launcher (NOT the real entry point).

The project's real `main.py` is missing from the repo (only `dist/main.exe` was
committed). This scaffold just instantiates the main window's layout so the UI can
be looked at on macOS. It does NOT wire up buttons, networking, MQTT, audio, or the
schedulers — those live in the missing main.py. Delete this once the real main.py arrives.

Usage:
    python preview_ui.py           # show the window (interactive)
    python preview_ui.py --shot    # render once to preview_ui.png and exit (for verification)
"""
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from src.ui.root.UI_MainWindow import Ui_MainWindow


def build_window() -> QMainWindow:
    win = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(win)
    win.setWindowTitle("KSB SG — UI preview (no logic wired)")
    return win


def main() -> int:
    app = QApplication(sys.argv)
    win = build_window()
    win.show()

    if "--shot" in sys.argv:
        app.processEvents()
        app.processEvents()
        win.grab().save("preview_ui.png")
        print("saved preview_ui.png")
        return 0

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
