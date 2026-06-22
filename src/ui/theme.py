# -*- coding: utf-8 -*-
"""
theme.py — единый источник правды для оформления клиента.

Содержит дизайн-токены (тёмная/светлая темы) и сборку одного общего
QSS-стиля для всего приложения. Применяется один раз:

    from src.ui.theme import app_stylesheet, tokens_for
    app.setStyleSheet(app_stylesheet("dark"))

Идея: вместо десятков `setStyleSheet` по месту виджеты получают облик через
общий стиль и `objectName`. Это и есть «единый вид» из редизайна.
Имена цветов согласованы с src/ui/Colors.py (бренд-синий #2979FE сохранён).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Tokens:
    bg: str        # фон окна
    card: str      # панели/карточки
    elev: str      # инпуты / hover-поверхности
    border: str
    text: str
    muted: str     # второстепенный текст
    accent: str    # акцент (бренд-синий)
    accent_h: str  # акцент hover
    accent_p: str  # акцент pressed
    danger: str
    danger_h: str
    online: str
    offline: str


# Бренд-синий из Colors.py (#2979FE) сохраняем как акцент в обеих темах.
DARK = Tokens(
    bg="#121419", card="#232b3a", elev="#2d3545", border="#3b4556",
    text="#e7eaf0", muted="#9aa3b3",
    accent="#2979FE", accent_h="#559CFE", accent_p="#0F2575",
    danger="#ef4444", danger_h="#dc2f2f",
    online="#22c55e", offline="#6b7280",
)

LIGHT = Tokens(
    bg="#e4e8f0", card="#ffffff", elev="#eef1f6", border="#d4d9e2",
    text="#1b1e24", muted="#6b7280",
    accent="#2979FE", accent_h="#559CFE", accent_p="#0F2575",
    danger="#ef4444", danger_h="#dc2f2f",
    online="#16a34a", offline="#9aa3b3",
)


def tokens_for(theme: str) -> Tokens:
    return LIGHT if theme == "light" else DARK


def app_stylesheet(theme: str = "dark") -> str:
    """Единый QSS для всего приложения, собранный из токенов выбранной темы."""
    t = tokens_for(theme)
    return f"""
* {{ font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 13px; color: {t.text}; }}
QMainWindow, QWidget#root {{ background: {t.bg}; }}

/* карточки */
QFrame#card {{ background: {t.card}; border: 1px solid {t.border}; border-radius: 12px; }}
QLabel#sectionTitle {{ color: {t.muted}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QLabel#panelTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#muted {{ color: {t.muted}; }}
QLabel#brandName {{ font-size: 16px; font-weight: 600; }}

/* кнопки */
QPushButton {{ background: {t.elev}; border: 1px solid {t.border}; border-radius: 8px;
               padding: 9px 14px; color: {t.text}; }}
QPushButton:hover {{ background: {t.border}; }}
QPushButton:pressed {{ background: {t.accent_p}; }}
QPushButton#primary {{ background: {t.accent}; border: none; color: white; font-weight: 600; padding: 12px 14px; }}
QPushButton#primary:hover {{ background: {t.accent_h}; }}
QPushButton#primary:pressed {{ background: {t.accent_p}; }}
QPushButton#ghost {{ background: transparent; }}
QPushButton#ghost:hover {{ background: {t.elev}; }}
QPushButton#danger {{ background: {t.danger}; border: none; color: white; font-weight: 600; }}
QPushButton#danger:hover {{ background: {t.danger_h}; }}
QPushButton#iconbtn {{ padding: 8px 12px; font-weight: 600; min-width: 18px; }}
QPushButton#record {{ background: {t.danger}; border: none; border-radius: 26px;
                      min-width: 52px; min-height: 52px; font-size: 20px; color: white; }}
QPushButton#record:hover {{ background: {t.danger_h}; }}
QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 4px; }}
QToolButton:hover {{ border-color: {t.accent}; }}

/* вкладки */
QTabWidget::pane {{ border: 1px solid {t.border}; border-radius: 10px; top: -1px; background: {t.card}; }}
QTabBar::tab {{ background: transparent; color: {t.muted}; padding: 8px 20px; margin-right: 4px;
                border-radius: 8px; font-weight: 600; }}
QTabBar::tab:selected {{ background: {t.accent}; color: white; }}
QTabBar::tab:hover:!selected {{ color: {t.text}; }}

/* инпуты */
QComboBox, QLineEdit, QSpinBox {{ background: {t.elev}; border: 1px solid {t.border};
        border-radius: 8px; padding: 6px 10px; }}
QComboBox:hover, QLineEdit:focus, QSpinBox:focus {{ border-color: {t.accent}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {t.elev}; border: 1px solid {t.border};
        selection-background-color: {t.accent}; outline: none; }}

/* чекбокс */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px;
        border: 1px solid {t.border}; background: {t.elev}; }}
QCheckBox::indicator:checked {{ background: {t.accent}; border-color: {t.accent}; }}

/* слайдер */
QSlider::groove:horizontal {{ height: 6px; background: {t.elev}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: white; width: 16px; height: 16px;
        margin: -6px 0; border-radius: 8px; }}

/* список файлов (QTableWidget) и список зон (QListWidget) — без рамок, прозрачный фон */
QTableWidget, QListWidget {{ background: transparent; border: none; gridline-color: transparent; }}
QTableWidget::item {{ background: transparent; padding: 0; }}
QListWidget::item {{ background: transparent; }}
QWidget#fileCard, QWidget#zoneCard {{ background: {t.card}; border: 1px solid {t.border}; border-radius: 12px; }}
QWidget#fileCard:hover, QWidget#zoneCard:hover {{ border-color: {t.accent}; }}

/* скроллбары */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.border}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t.muted}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""
