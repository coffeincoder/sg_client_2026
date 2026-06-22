# -*- coding: utf-8 -*-
"""
preview_real.py — превью редизайна на НАСТОЯЩИХ виджетах проекта.

В отличие от preview_redesign.py (пустышка с фейковыми виджетами), здесь
используются реальные FileListWidget / ZoneListWidget / FileListItem /
ZoneListItem с демо-данными и применяется общий стиль из src/ui/theme.py.

Реальные main.py и UI_MainWindow.py НЕ трогаются — это изолированная витрина,
чтобы оценить вид до переноса в боевое окно.

Запуск:
    .venv/bin/python preview_real.py            # живое окно
    QT_QPA_PLATFORM=offscreen .venv/bin/python preview_real.py --shot   # рендер в preview_real.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QSlider, QCheckBox,
    QSpinBox, QFrame, QVBoxLayout, QHBoxLayout, QTabWidget, QLineEdit, QSizePolicy,
)

from src.ui.theme import app_stylesheet
from src.data.FileModel import FileItem
from src.data.ZoneModel import Orange
from src.ui.custom.file.FileListWidget import FileListWidget
from src.ui.custom.zone.ZoneListWidget import ZoneListWidget

THEME = "dark"

SAMPLE_FILES = [
    FileItem(header="Объявление о пожаре", filename="fire.mp3",
             text="Внимание! Просьба сохранять спокойствие и проследовать к ближайшему выходу.",
             duration=23, create_date="12.06.2026", current_voice="fg"),
    FileItem(header="Гимн организации", filename="hymn.mp3",
             text="Торжественный текст гимна для воспроизведения на мероприятиях.",
             duration=134, create_date="10.06.2026", current_voice="an"),
    FileItem(header="Реклама — акция", filename="promo.mp3",
             text="Только сегодня — специальное предложение для наших клиентов!",
             duration=45, create_date="09.06.2026", current_voice="fn"),
]

SAMPLE_ZONES = [
    Orange(name="Главный вход", ip="192.168.1.21", isChecked=True, is_online=True,
           is_playing=True, subzone1=True, subzone1_name="Канал 1", subzone2_name="Канал 2"),
    Orange(name="Склад №2", ip="192.168.1.22", isChecked=True, is_online=True,
           subzone1_name="Левый", subzone2_name="Правый"),
    Orange(name="Офис, 3 этаж", ip="192.168.1.23", isChecked=False, is_online=False,
           subzone1_name="Канал 1", subzone2_name="Канал 2"),
]


def card() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionTitle")
    return lbl


def build_left() -> QWidget:
    w = QWidget()
    w.setFixedWidth(300)
    col = QVBoxLayout(w)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(14)

    # бренд
    brand = QHBoxLayout()
    brand.setSpacing(10)
    logo = QLabel("КБ")
    logo.setFixedSize(44, 44)
    logo.setAlignment(Qt.AlignCenter)
    logo.setStyleSheet("background: #2979FE; border-radius: 22px; color: white; font-weight: 700; font-size: 16px;")
    name = QLabel("Sound Guard")
    name.setObjectName("brandName")
    brand.addWidget(logo)
    brand.addWidget(name)
    brand.addStretch()
    col.addLayout(brand)

    # карточка воспроизведения
    pc = card()
    pcl = QVBoxLayout(pc)
    pcl.setContentsMargins(16, 16, 16, 16)
    pcl.setSpacing(12)
    pcl.addWidget(section_label("Воспроизведение"))
    play = QPushButton("▶  Проиграть")
    play.setObjectName("primary")
    stop = QPushButton("■  Остановить")
    pcl.addWidget(play)
    pcl.addWidget(stop)

    vol_row = QHBoxLayout()
    vlab = QLabel("Громкость")
    vlab.setObjectName("muted")
    vval = QLabel("72%")
    vval.setObjectName("muted")
    vval.setAlignment(Qt.AlignRight)
    vol_row.addWidget(vlab)
    vol_row.addWidget(vval)
    pcl.addLayout(vol_row)
    vol = QSlider(Qt.Horizontal)
    vol.setValue(72)
    pcl.addWidget(vol)

    rep_row = QHBoxLayout()
    rep = QCheckBox("Повторять")
    rep.setChecked(True)
    spin = QSpinBox()
    spin.setRange(0, 99)
    spin.setValue(3)
    spin.setFixedWidth(64)
    rep_row.addWidget(rep)
    rep_row.addStretch()
    rep_row.addWidget(QLabel("раз"))
    rep_row.addWidget(spin)
    pcl.addLayout(rep_row)
    col.addWidget(pc)

    # карточка трансляции
    bc = card()
    bcl = QVBoxLayout(bc)
    bcl.setContentsMargins(16, 16, 16, 16)
    bcl.setSpacing(12)
    head = QHBoxLayout()
    head.addWidget(section_label("Трансляция"))
    head.addStretch()
    rec = QPushButton("🎙")
    rec.setObjectName("record")
    head.addWidget(rec)
    bcl.addLayout(head)
    talk = QPushButton("🔴  Говорить с микрофона")
    stoptalk = QPushButton("Прекратить вещание")
    stoptalk.setObjectName("ghost")
    bcl.addWidget(talk)
    bcl.addWidget(stoptalk)
    col.addWidget(bc)

    col.addStretch()
    return w


def build_center() -> QWidget:
    w = QWidget()
    col = QVBoxLayout(w)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(12)

    tabs = QTabWidget()
    files_tab = QWidget()
    ftl = QVBoxLayout(files_tab)
    ftl.setContentsMargins(14, 14, 14, 14)
    ftl.setSpacing(12)

    # тулбар: поиск + сортировка
    tb = QHBoxLayout()
    tb.setSpacing(8)
    search = QLineEdit()
    search.setPlaceholderText("🔎  Поиск файла…")
    sort_name = QPushButton("По имени  A↓")
    sort_name.setObjectName("ghost")
    sort_date = QPushButton("По дате  ⌄")
    sort_date.setObjectName("ghost")
    tb.addWidget(search, 1)
    tb.addWidget(sort_name)
    tb.addWidget(sort_date)
    ftl.addLayout(tb)

    # реальный список файлов с демо-данными
    file_list = FileListWidget()
    file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    file_list.update_file_list(SAMPLE_FILES, grid_size=1)
    ftl.addWidget(file_list, 1)

    # кнопки добавления
    add = QHBoxLayout()
    add.setSpacing(8)
    a1 = QPushButton("＋  Загрузить аудиофайл")
    a1.setObjectName("primary")
    a2 = QPushButton("🎙  Записать с микрофона")
    a3 = QPushButton("🗣  Озвучить из текста")
    add.addWidget(a1)
    add.addWidget(a2)
    add.addWidget(a3)
    ftl.addLayout(add)

    tabs.addTab(files_tab, "Файлы")

    scen = QWidget()
    sl = QVBoxLayout(scen)
    sl.setContentsMargins(14, 14, 14, 14)
    ph = QLabel("Здесь список сценариев")
    ph.setObjectName("muted")
    ph.setAlignment(Qt.AlignCenter)
    sl.addWidget(ph)
    tabs.addTab(scen, "Сценарии")

    col.addWidget(tabs)
    return w


def build_right() -> QWidget:
    w = QWidget()
    w.setFixedWidth(340)
    col = QVBoxLayout(w)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(12)

    head = QHBoxLayout()
    t = QLabel("Зоны-Устройства")
    t.setObjectName("panelTitle")
    head.addWidget(t)
    head.addStretch()
    for txt, tip in (("⌕", "Авто-поиск"), ("＋", "Добавить"), ("⟳", "Обновить")):
        b = QPushButton(txt)
        b.setObjectName("iconbtn")
        b.setToolTip(tip)
        head.addWidget(b)
    col.addLayout(head)

    # реальный список зон с демо-данными
    zone_list = ZoneListWidget()
    zone_list.update_zones(SAMPLE_ZONES)
    col.addWidget(zone_list, 1)
    return w


def build_window() -> QMainWindow:
    win = QMainWindow()
    win.setWindowTitle("КСБ Саундгард — превью редизайна (реальные виджеты)")
    win.resize(1440, 920)
    win.setMinimumSize(1180, 760)
    root = QWidget()
    root.setObjectName("root")
    row = QHBoxLayout(root)
    row.setContentsMargins(18, 18, 18, 18)
    row.setSpacing(16)
    row.addWidget(build_left())
    row.addWidget(build_center(), 1)
    row.addWidget(build_right())
    win.setCentralWidget(root)
    return win


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet(THEME))
    win = build_window()
    win.show()
    if "--shot" in sys.argv:
        app.processEvents()
        app.processEvents()
        win.grab().save("preview_real.png")
        print("saved preview_real.png")
        return 0
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
