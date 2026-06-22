# -*- coding: utf-8 -*-
"""
preview_real.py — превью редизайна на НАСТОЯЩИХ виджетах проекта.

Использует реальные FileListWidget / ZoneListWidget / FileListItem /
ZoneListItem с демо-данными и общий стиль из src/ui/theme.py.
Только bundled PNG-иконки (res/IMAGES) — без эмодзи, чтобы на всех клиентах
иконки выглядели одинаково, а не превращались в «кракозябры».

Реальные main.py и UI_MainWindow.py НЕ трогаются.

Запуск:
    .venv/bin/python preview_real.py
    QT_QPA_PLATFORM=offscreen .venv/bin/python preview_real.py --shot
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont
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
IMG = os.path.join(BASE, "res", "IMAGES")


def _icon(name: str) -> QIcon:
    return QIcon(os.path.join(IMG, name))


def make_btn(text="", icon_name=None, obj=None, icon_px=26, min_h=44) -> QPushButton:
    b = QPushButton(text)
    if obj:
        b.setObjectName(obj)
    if icon_name:
        b.setIcon(_icon(icon_name))
        b.setIconSize(QSize(icon_px, icon_px))
    b.setMinimumHeight(min_h)
    return b


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
    w.setFixedWidth(310)
    col = QVBoxLayout(w)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(16)

    # бренд — настоящий логотип, без кислотного кружка
    brand = QHBoxLayout()
    brand.setSpacing(12)
    logo = QLabel()
    pm = QPixmap(os.path.join(IMG, "logo (2).png"))
    if not pm.isNull():
        logo.setPixmap(pm.scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    name = QLabel("Sound Guard")
    name.setObjectName("brandName")
    brand.addWidget(logo)
    brand.addWidget(name)
    brand.addStretch()
    col.addLayout(brand)

    # карточка воспроизведения — единственный яркий акцент (главное действие)
    pc = card()
    pcl = QVBoxLayout(pc)
    pcl.setContentsMargins(16, 16, 16, 16)
    pcl.setSpacing(12)
    pcl.addWidget(section_label("Воспроизведение"))
    play = make_btn("  Проиграть", "cast-audio-custom (1).png", obj="primary", icon_px=30, min_h=54)
    stop = make_btn("Остановить", min_h=46)
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
    spin.setFixedWidth(70)
    rep_row.addWidget(rep)
    rep_row.addStretch()
    rep_row.addWidget(QLabel("раз"))
    rep_row.addWidget(spin)
    pcl.addLayout(rep_row)
    col.addWidget(pc)

    # карточка трансляции — спокойные кнопки с иконками
    bc = card()
    bcl = QVBoxLayout(bc)
    bcl.setContentsMargins(16, 16, 16, 16)
    bcl.setSpacing(12)
    bcl.addWidget(section_label("Трансляция"))
    talk = make_btn("  Говорить с микрофона", "broadcast-custom (1).png", icon_px=28, min_h=50)
    stoptalk = make_btn("  Прекратить вещание", "broadcast-off-custom.png", obj="ghost", icon_px=26, min_h=46)
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

    # тулбар: поиск + сортировка (без эмодзи)
    tb = QHBoxLayout()
    tb.setSpacing(8)
    search = QLineEdit()
    search.setPlaceholderText("Поиск файла…")
    search.setMinimumHeight(40)
    sort_name = make_btn(" По имени", "sort1.png", obj="ghost", icon_px=22, min_h=40)
    sort_date = make_btn(" По дате", "sort1.png", obj="ghost", icon_px=22, min_h=40)
    tb.addWidget(search, 1)
    tb.addWidget(sort_name)
    tb.addWidget(sort_date)
    ftl.addLayout(tb)

    # реальный список файлов с демо-данными
    file_list = FileListWidget()
    file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    file_list.update_file_list(SAMPLE_FILES, grid_size=1)
    ftl.addWidget(file_list, 1)

    # кнопки добавления — крупные иконки
    add = QHBoxLayout()
    add.setSpacing(8)
    a1 = make_btn("  Загрузить аудиофайл", "arrow-up.png", obj="primary", icon_px=24, min_h=50)
    a2 = make_btn("  Записать с микрофона", "microphone.png", icon_px=26, min_h=50)
    a3 = make_btn("  Озвучить из текста", "text-to-speech.png", icon_px=26, min_h=50)
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
    w.setFixedWidth(350)
    col = QVBoxLayout(w)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(12)

    # заголовок отдельной строкой
    head = QHBoxLayout()
    t = QLabel("Зоны-Устройства")
    t.setObjectName("panelTitle")
    head.addWidget(t)
    head.addStretch()
    col.addLayout(head)

    # понятная панель действий с подписями (как в боевом zone_buttons_layout)
    tools = QHBoxLayout()
    tools.setSpacing(8)
    find = make_btn("Найти", min_h=44)
    find.setToolTip("Авто-поиск устройств в сети")
    add_zone = make_btn("+  Добавить", min_h=44)
    add_zone.setToolTip("Добавить зону вручную")
    refresh = make_btn("Обновить", "refresh.png", icon_px=22, min_h=44)
    refresh.setToolTip("Обновить связь с зонами")
    big = QFont()
    big.setPointSize(11)
    for b in (find, add_zone, refresh):
        b.setFont(big)
        tools.addWidget(b)
    col.addLayout(tools)

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
