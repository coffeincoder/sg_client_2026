# -*- coding: utf-8 -*-
"""ElidingLabel — QLabel, обрезающий длинный текст многоточием (…).

В отличие от setWordWrap(True), корректно ужимает и длинные слова без пробелов
(например пользовательские названия вида «Вашепредупреждениеэтонеошибка»),
которые перенос по словам разбить не может и потому обрезал по краю карточки.

Полный текст показывается во всплывающей подсказке. Пересчёт при каждом
изменении ширины — работает и в 1 колонку (широкие карточки), и в 2-4 (узкие).
"""
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize


class ElidingLabel(QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = text
        # Ignored по ширине: layout волен сжимать лейбл ниже ширины текста.
        # Иначе QLabel держит ширину всего текста и распирает карточку.
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setToolTip(text)
        self._apply_elided()

    def setText(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._apply_elided()

    def full_text(self) -> str:
        return self._full_text

    def minimumSizeHint(self) -> QSize:
        # Не требуем ширины всего текста — только высоту строки.
        return QSize(0, self.fontMetrics().height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_elided()

    def _apply_elided(self) -> None:
        fm = self.fontMetrics()
        avail = max(self.width() - 2, 0)
        super().setText(fm.elidedText(self._full_text, Qt.ElideRight, avail))
