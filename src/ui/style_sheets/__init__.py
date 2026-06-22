# StyleSheets.py
import json

import paths
from src.ui import Colors
from src.ui.theme import tokens_for


def _get_theme():
    with open(paths.settings) as s:
        return json.load(s)["theme"]


def _get_colors():
    theme = _get_theme()
    if theme == "light":
        return Colors.Light
    elif theme == "dark":
        return Colors.Dark


def _t():
    """Токены оформления текущей темы (src/ui/theme.py)."""
    return tokens_for(_get_theme())


# Элементы списка
# Подписи под файлом (длительность / дата / голос) — лёгкие «чипы», без рамок-коробок.

def duration_label_style():
    t = _t()
    return f'''
    QLabel {{
        background-color: {t.elev};
        color: {t.muted};
        padding: 3px 8px;
        border: none;
        border-radius: 6px;
    }}
'''


def create_date_label_style1():
    """Без плашки с голосом — единый стиль чипа."""
    return duration_label_style()


def create_date_label_style2():
    """С плашкой голоса — тот же чип (рамок-сегментов больше нет)."""
    return duration_label_style()


def voice_label_style():
    t = _t()
    return f'''
            QLabel {{
                background-color: {t.elev};
                color: {t.accent};
                padding: 3px 8px;
                border: none;
                border-radius: 6px;
            }}
        '''


def file_list_item_style():
    # Облик карточки задаётся общим QSS (QWidget#fileCard) в src/ui/theme.py.
    return ""


def list_widget_item_style():
    return '''
        QTableWidget { background: transparent; border: none; }
        QTableWidget::item {
            background-color: transparent;
            padding: 0px;
            margin-bottom: 10px;
        }
        QTableWidget::item:selected {
            background-color: transparent;
        }
    '''


def list_widget_header_style():
    # Плоский заголовок карточки: жирно, без синей рамки-коробки.
    t = _t()
    return f'''
            border: none;
            background: transparent;
            color: {t.text};
            padding: 2px 0px;
            font-weight: bold;
        '''


def scroll_label_list_item_style():
    # Область текста файла — прозрачная, сливается с карточкой.
    return '''
           background-color: transparent;
        '''


def scroll_label_list_item_text_style():
    t = _t()
    return f'''
            * {{
                background-color: transparent;
                color: {t.muted};
                padding: 4px 0px;
                font: italic 10pt 'Tahoma';
            }}
           '''


# zones

def zone_list_item_style():
    # Облик карточки зоны задаётся общим QSS (QWidget#zoneCard) в src/ui/theme.py.
    return ""


def spin_box_text_size():
    return "QSpinBox { font-size: 18px; }"


def volume_slider_style_default():
    t = _t()
    return f'''
               QSlider::handle:horizontal {{ background-color: white; }}
               QSlider::sub-page:horizontal {{ background-color: {t.accent}; }}
           '''


def volume_slider_style_overload():
    t = _t()
    return f'''
               QSlider::handle:horizontal {{ background-color: white; }}
               QSlider::sub-page:horizontal {{ background-color: {t.danger}; }}
           '''


# кнопки

def blue_color_btn():
    t = _t()
    return f"""
             QPushButton {{
                    background-color: {t.accent};
                    color: white;
                    border: none;
                    border-radius: 8px;
                }}
             QPushButton:pressed {{ background-color: {t.accent_p}; }}
             QPushButton:hover {{ background-color: {t.accent_h}; }}
            """


def zone_item_btn():
    t = _t()
    return f"""
             QPushButton {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 8px;
                }}
             QPushButton:hover {{ border-color: {t.accent}; }}
             QPushButton:pressed {{ background-color: {t.elev}; }}
            """


def stop_realtime_btn_state1():
    t = _t()
    return f"""
            QPushButton {{ background-color: {t.elev}; border: 1px solid {t.border}; border-radius: 8px; }}
            QPushButton:hover {{ background-color: {t.border}; }}
            QPushButton:pressed {{ background-color: {t.accent_p}; }}
            """


def stop_realtime_btn_state2():
    t = _t()
    return f"""
            QPushButton {{ background-color: {t.danger}; color: white; border: none; border-radius: 8px; }}
            QPushButton:hover {{ background-color: {t.danger_h}; }}
            """


def button_style():
    t = _t()
    return f'''
        QPushButton {{
            background-color: {t.elev};
            border: 1px solid {t.border};
            border-radius: 8px;
            padding: 6px;
        }}
        QPushButton:hover {{ background-color: {t.border}; }}
        QPushButton:pressed {{ background-color: {t.accent_p}; }}
    '''
