"""
preview_redesign.py — a tidied-up, self-contained redesign of the KSB SG client window.

This does NOT touch the real project files. The original `src/ui/root/UI_MainWindow.py`
is left intact so the (incoming) real `main.py` keeps working. This file rebuilds the
SAME functional areas — playback, broadcast, files/scenarios, zones — but with clean
layout, spacing, a single cohesive stylesheet, fixed proportions, and sample data so the
lists look alive instead of empty.

Usage:
    .venv/bin/python preview_redesign.py          # live window
    .venv/bin/python preview_redesign.py --shot    # render to preview_redesign.png and exit
"""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QSlider, QCheckBox,
    QSpinBox, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox, QLineEdit,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
)

# ---- design tokens -----------------------------------------------------------
BG       = "#1b1e24"   # window
CARD     = "#232730"   # panels / cards
ELEV     = "#2b303b"   # inputs / hover
BORDER   = "#363c49"
TEXT     = "#e7eaf0"
MUTED    = "#9aa3b3"
ACCENT   = "#3b82f6"
ACCENT_H = "#2f6fe0"
DANGER   = "#ef4444"
DANGER_H = "#dc2f2f"
ONLINE   = "#22c55e"
OFFLINE  = "#6b7280"

STYLE = f"""
* {{ font-family: 'Helvetica Neue', 'Segoe UI', Arial, sans-serif; font-size: 13px; color: {TEXT}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}

QFrame#card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#sectionTitle {{ color: {MUTED}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QLabel#panelTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#muted {{ color: {MUTED}; }}

/* buttons */
QPushButton {{ background: {ELEV}; border: 1px solid {BORDER}; border-radius: 8px;
               padding: 9px 14px; color: {TEXT}; }}
QPushButton:hover {{ background: #323845; }}
QPushButton:pressed {{ background: #3a4150; }}
QPushButton#primary {{ background: {ACCENT}; border: none; font-weight: 600; padding: 12px 14px; }}
QPushButton#primary:hover {{ background: {ACCENT_H}; }}
QPushButton#ghost {{ background: transparent; }}
QPushButton#ghost:hover {{ background: {ELEV}; }}
QPushButton#danger {{ background: {DANGER}; border: none; font-weight: 600; }}
QPushButton#danger:hover {{ background: {DANGER_H}; }}
QPushButton#iconbtn {{ padding: 8px 12px; font-weight: 600; min-width: 20px; }}
QPushButton#record {{ background: {DANGER}; border: none; border-radius: 26px;
                      min-width: 52px; min-height: 52px; font-size: 20px; }}
QPushButton#record:hover {{ background: {DANGER_H}; }}

/* tabs */
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; top: -1px; background: {CARD}; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 20px; margin-right: 4px;
                border-radius: 8px; font-weight: 600; }}
QTabBar::tab:selected {{ background: {ACCENT}; color: white; }}
QTabBar::tab:hover:!selected {{ color: {TEXT}; }}

/* inputs */
QComboBox, QLineEdit, QSpinBox {{ background: {ELEV}; border: 1px solid {BORDER};
        border-radius: 8px; padding: 6px 10px; }}
QComboBox:hover, QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {ELEV}; border: 1px solid {BORDER};
        selection-background-color: {ACCENT}; outline: none; }}

/* checkbox */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px;
        border: 1px solid {BORDER}; background: {ELEV}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

/* slider */
QSlider::groove:horizontal {{ height: 6px; background: {ELEV}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: white; width: 16px; height: 16px;
        margin: -6px 0; border-radius: 8px; }}

/* table */
QTableWidget {{ background: {CARD}; border: none; gridline-color: transparent; }}
QTableWidget::item {{ padding: 10px 8px; border-bottom: 1px solid {BORDER}; }}
QTableWidget::item:selected {{ background: {ELEV}; color: {TEXT}; }}
QHeaderView::section {{ background: transparent; color: {MUTED}; border: none;
        border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 600; text-align: left; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""

SAMPLE_FILES = [
    ("Объявление о пожаре.mp3", "00:23", "12.06.2026"),
    ("Гимн организации.mp3",    "02:14", "10.06.2026"),
    ("Реклама — акция.mp3",     "00:45", "09.06.2026"),
    ("Эвакуация.wav",           "00:31", "08.06.2026"),
    ("Тестовый сигнал.wav",     "00:05", "05.06.2026"),
]
SAMPLE_ZONES = [
    ("Главный вход",  True,  "Гимн организации",    "—"),
    ("Склад №2",      True,  "Реклама — акция",      "Тестовый сигнал"),
    ("Офис, 3 этаж",  False, "—",                    "—"),
    ("Парковка",      True,  "Объявление о пожаре",  "—"),
]


def card(*, radius=12) -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    sh = QGraphicsDropShadowEffect(f)
    sh.setBlurRadius(24); sh.setXOffset(0); sh.setYOffset(4)
    sh.setColor(QColor(0, 0, 0, 60))
    f.setGraphicsEffect(sh)
    return f


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper()); lbl.setObjectName("sectionTitle")
    return lbl


# ---- left: playback + broadcast ---------------------------------------------
def build_left() -> QWidget:
    w = QWidget(); w.setFixedWidth(280)
    col = QVBoxLayout(w); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(14)

    # brand
    brand = QHBoxLayout(); brand.setSpacing(10)
    logo = QLabel("КБ"); logo.setFixedSize(44, 44); logo.setAlignment(Qt.AlignCenter)
    logo.setStyleSheet(f"background: {ACCENT}; border-radius: 22px; font-weight: 700; font-size: 16px;")
    name = QLabel("Sound Guard"); name.setStyleSheet("font-size: 16px; font-weight: 600;")
    brand.addWidget(logo); brand.addWidget(name); brand.addStretch()
    col.addLayout(brand)

    # playback card
    pc = card(); pcl = QVBoxLayout(pc); pcl.setContentsMargins(16, 16, 16, 16); pcl.setSpacing(12)
    pcl.addWidget(section_label("Воспроизведение"))
    play = QPushButton("▶  Проиграть"); play.setObjectName("primary")
    stop = QPushButton("■  Остановить")
    pcl.addWidget(play); pcl.addWidget(stop)

    vol_row = QHBoxLayout()
    vlab = QLabel("Громкость"); vlab.setObjectName("muted")
    vval = QLabel("72%"); vval.setObjectName("muted"); vval.setAlignment(Qt.AlignRight)
    vol_row.addWidget(vlab); vol_row.addWidget(vval)
    pcl.addLayout(vol_row)
    vol = QSlider(Qt.Horizontal); vol.setValue(72)
    pcl.addWidget(vol)

    rep_row = QHBoxLayout()
    rep = QCheckBox("Повторять"); rep.setChecked(True)
    spin = QSpinBox(); spin.setRange(0, 99); spin.setValue(3); spin.setFixedWidth(64)
    rep_row.addWidget(rep); rep_row.addStretch(); rep_row.addWidget(QLabel("раз")); rep_row.addWidget(spin)
    pcl.addLayout(rep_row)
    col.addWidget(pc)

    # broadcast card
    bc = card(); bcl = QVBoxLayout(bc); bcl.setContentsMargins(16, 16, 16, 16); bcl.setSpacing(12)
    head = QHBoxLayout()
    head.addWidget(section_label("Трансляция")); head.addStretch()
    rec = QPushButton("🎙"); rec.setObjectName("record")
    head.addWidget(rec)
    bcl.addLayout(head)
    talk = QPushButton("🔴  Говорить с микрофона")
    stoptalk = QPushButton("Прекратить вещание"); stoptalk.setObjectName("ghost")
    bcl.addWidget(talk); bcl.addWidget(stoptalk)
    col.addWidget(bc)

    col.addStretch()
    return w


# ---- center: files / scenarios ----------------------------------------------
def build_center() -> QWidget:
    w = QWidget()
    col = QVBoxLayout(w); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(12)

    tabs = QTabWidget()
    files_tab = QWidget(); ftl = QVBoxLayout(files_tab)
    ftl.setContentsMargins(14, 14, 14, 14); ftl.setSpacing(12)

    # toolbar
    tb = QHBoxLayout(); tb.setSpacing(8)
    search = QLineEdit(); search.setPlaceholderText("🔎  Поиск файла…")
    sort_name = QPushButton("По имени  A↓"); sort_name.setObjectName("ghost")
    sort_date = QPushButton("По дате  ⌄");   sort_date.setObjectName("ghost")
    tb.addWidget(search, 1); tb.addWidget(sort_name); tb.addWidget(sort_date)
    ftl.addLayout(tb)

    # table
    table = QTableWidget(len(SAMPLE_FILES), 3)
    table.setHorizontalHeaderLabels(["Название", "Длит.", "Дата"])
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setShowGrid(False)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    table.setColumnWidth(1, 80); table.setColumnWidth(2, 110)
    for r, (n, d, dt) in enumerate(SAMPLE_FILES):
        table.setItem(r, 0, QTableWidgetItem("🎵  " + n))
        dur = QTableWidgetItem(d); dur.setForeground(QColor(MUTED))
        date = QTableWidgetItem(dt); date.setForeground(QColor(MUTED))
        table.setItem(r, 1, dur); table.setItem(r, 2, date)
        table.setRowHeight(r, 44)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.selectRow(0)
    ftl.addWidget(table, 1)

    # add-file actions
    add = QHBoxLayout(); add.setSpacing(8)
    a1 = QPushButton("＋  Загрузить аудиофайл"); a1.setObjectName("primary")
    a2 = QPushButton("🎙  Записать с микрофона")
    a3 = QPushButton("🗣  Озвучить из текста")
    add.addWidget(a1); add.addWidget(a2); add.addWidget(a3)
    ftl.addLayout(add)

    tabs.addTab(files_tab, "Файлы")
    scen = QWidget(); sl = QVBoxLayout(scen); sl.setContentsMargins(14, 14, 14, 14)
    ph = QLabel("Здесь список сценариев"); ph.setObjectName("muted"); ph.setAlignment(Qt.AlignCenter)
    sl.addWidget(ph)
    tabs.addTab(scen, "Сценарии")
    col.addWidget(tabs)
    return w


# ---- right: zones / devices --------------------------------------------------
def zone_row(name: str, online: bool, ch1: str, ch2: str) -> QFrame:
    f = card(); f.setMaximumHeight(120)
    lay = QVBoxLayout(f); lay.setContentsMargins(14, 12, 14, 12); lay.setSpacing(8)
    top = QHBoxLayout()
    dot = QLabel("●"); dot.setStyleSheet(f"color: {ONLINE if online else OFFLINE}; font-size: 12px;")
    nm = QLabel(name); nm.setStyleSheet("font-weight: 600;")
    status = QLabel("онлайн" if online else "офлайн"); status.setObjectName("muted")
    top.addWidget(dot); top.addWidget(nm); top.addStretch(); top.addWidget(status)
    lay.addLayout(top)
    grid = QGridLayout(); grid.setSpacing(6)
    for i, (lbl, val) in enumerate([("Канал 1", ch1), ("Канал 2", ch2)]):
        l = QLabel(lbl); l.setObjectName("muted")
        cb = QComboBox(); cb.addItem(val); cb.setEnabled(online)
        grid.addWidget(l, i, 0); grid.addWidget(cb, i, 1)
    grid.setColumnStretch(1, 1)
    lay.addLayout(grid)
    return f


def build_right() -> QWidget:
    w = QWidget(); w.setFixedWidth(330)
    col = QVBoxLayout(w); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(12)
    head = QHBoxLayout()
    t = QLabel("Зоны-Устройства"); t.setObjectName("panelTitle")
    head.addWidget(t); head.addStretch()
    for txt in ("⌕", "＋", "⟳"):
        b = QPushButton(txt); b.setObjectName("iconbtn"); head.addWidget(b)
    col.addLayout(head)

    scroll = QScrollArea(); scroll.setWidgetResizable(True)
    inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 6, 0); il.setSpacing(10)
    for z in SAMPLE_ZONES:
        il.addWidget(zone_row(*z))
    il.addStretch()
    scroll.setWidget(inner)
    col.addWidget(scroll, 1)
    return w


def build_window() -> QMainWindow:
    win = QMainWindow()
    win.setWindowTitle("KSB SG — UI redesign (preview)")
    win.resize(1240, 780)
    root = QWidget(); root.setObjectName("root")
    row = QHBoxLayout(root)
    row.setContentsMargins(18, 18, 18, 18); row.setSpacing(16)
    row.addWidget(build_left())
    row.addWidget(build_center(), 1)
    row.addWidget(build_right())
    win.setCentralWidget(root)
    return win


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    win = build_window()
    win.show()
    if "--shot" in sys.argv:
        app.processEvents(); app.processEvents()
        win.grab().save("preview_redesign.png")
        print("saved preview_redesign.png")
        return 0
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
