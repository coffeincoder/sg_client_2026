# -*- coding: utf-8 -*-
"""
gen_ui_icons.py — генерация недостающих белых UI-иконок в res/IMAGES.

В ассетах нет шестерёнки, галочки и стрелок для спинбокса, а часть иконок
чёрные (невидимы на тёмной теме). Этот скрипт рисует их белыми с прозрачным
фоном через QPainter — повторяемо, без внешних зависимостей.

Запуск:
    QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/gen_ui_icons.py
"""
import os
import sys

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QApplication

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "res", "IMAGES")
WHITE = QColor("#ffffff")


def _canvas(size):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    return pm, p


def gear(size=64):
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    p.setBrush(WHITE)
    c = size / 2
    p.translate(c, c)
    R = size * 0.30          # радиус тела
    tw, th = size * 0.16, size * 0.16
    for i in range(8):       # зубья
        p.save()
        p.rotate(i * 45)
        p.drawRoundedRect(QRectF(-tw / 2, -R - th * 0.6, tw, th * 1.3), 2, 2)
        p.restore()
    p.drawEllipse(QPointF(0, 0), R, R)
    p.setCompositionMode(QPainter.CompositionMode_Clear)   # отверстие
    p.drawEllipse(QPointF(0, 0), R * 0.42, R * 0.42)
    p.end()
    pm.save(os.path.join(OUT, "ic-gear.png"))


def check(size=18):
    pm, p = _canvas(size)
    pen = QPen(WHITE)
    pen.setWidthF(size * 0.14)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    path = QPainterPath()
    path.moveTo(size * 0.22, size * 0.54)
    path.lineTo(size * 0.42, size * 0.74)
    path.lineTo(size * 0.80, size * 0.30)
    p.drawPath(path)
    p.end()
    pm.save(os.path.join(OUT, "ic-check.png"))


def chevron(name, up=True, size=12):
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    p.setBrush(WHITE)
    m = size * 0.22
    if up:
        tri = QPolygonF([QPointF(m, size - m), QPointF(size - m, size - m), QPointF(size / 2, m)])
    else:
        tri = QPolygonF([QPointF(m, m), QPointF(size - m, m), QPointF(size / 2, size - m)])
    p.drawPolygon(tri)
    p.end()
    pm.save(os.path.join(OUT, name))


def main():
    app = QApplication(sys.argv)
    gear()
    check()
    chevron("ic-chevron-up.png", up=True)
    chevron("ic-chevron-down.png", up=False)
    print("generated:", ", ".join(["ic-gear.png", "ic-check.png", "ic-chevron-up.png", "ic-chevron-down.png"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
