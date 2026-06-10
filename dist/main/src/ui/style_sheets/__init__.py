# StyleSheets.py
import json

import paths
from src.ui import Colors


def _get_theme():
    with open(paths.settings) as s:
        return json.load(s)["theme"]


def _get_colors():
    theme = _get_theme()
    if theme == "light":
        return Colors.Light
    elif theme == "dark":
        return Colors.Dark


# Элементы списка

def duration_label_style():
    colors = _get_colors()
    return f'''
    QLabel {{
        background-color: {colors.background_color};
        padding-left: 5px;
        padding: 5px;
        border: 1px solid {colors.blue};
        border-right: none;
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
    }}
'''


def create_date_label_style1():
    """Если нет плашки с голосом для файла"""
    colors = _get_colors()
    return f'''
                QLabel {{
                    background-color: {colors.background_color};
                    padding-left: 5px;
                    padding: 5px;
                    border: 1px solid {colors.blue};
                    border-left: none;
                    border-top-right-radius: 10px;
                    border-bottom-right-radius: 10px;
                }}
            '''  #


def create_date_label_style2():
    """Если есть плашка с голосом для файла"""
    colors = _get_colors()
    return f'''
                QLabel {{
                    background-color: {colors.background_color};
                    padding-left: 5px;
                    padding: 5px;
                    border-top: 1px solid {colors.blue};
                    border-bottom: 1px solid {colors.blue};
                }}
            '''


def voice_label_style():
    colors = _get_colors()
    return f'''
            QLabel {{
                background-color: {colors.background_color};
                padding-left: 5px;
                padding: 5px;
                border: 1px solid #2979FE;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border-left: none;
            }}
        '''


def file_list_item_style():
    return f'''
        padding:-1px;
    '''


def list_widget_item_style():
    colors = _get_colors()
    return f'''
        QTableWidget::item:selected {{
            border: 4px solid {colors.pressed_red};
            border-radius: 10px;
            background-color: {colors.gray};            
        }}
        QTableWidget::item {{
            background-color: {colors.background_color};
            border-radius: 15px;
            padding: 0px;
            margin-bottom: 10px;
            margin-top: 10px
        }}
        QTableWidget::item:hover {{
             background-color: {colors.hovered_gray};  
        }}
    '''


def list_widget_header_style():
    colors = _get_colors()
    return f'''
            border: 1px solid {colors.blue};
            border-radius: 8px;
            padding: 10px;
            padding-left: 15px;
            font-weight: bold;
        '''


def scroll_label_list_item_style():
    colors = _get_colors()
    return f'''
           background-color: {colors.background_color};
           border-radius: 10px;
           QLabel {{
               background-color: {colors.background_color};
           }}
           QLabel:hover {{
               background-color: {colors.background_color};
               font: italic 14pt 'Tahoma';
           }}
        '''  # это элемент внутри элемента главного списка, где расположен текст файла


def scroll_label_list_item_text_style():
    return f'''
            * {{
                padding: 5px;
                font: italic 10pt 'Tahoma';
            }}
                          
           '''


# ...

# zones

def zone_list_item_style():
    colors = _get_colors()
    return f"""
               border-radius: 8px;
               border: 2px solid {colors.background_color};
            """


def spin_box_text_size():
    return f'''
    QSpinBox {{ font-size: 26px; }}
    '''


def volume_slider_style_default():
    colors = _get_colors()
    return f'''
               QSlider::handle:horizontal {{ background-color: {colors.blue}; }}
           '''


def volume_slider_style_overload():
    colors = _get_colors()
    return f'''
               QSlider::handle:horizontal {{ background-color: {colors.red}; }}
           '''


# кнопки

def blue_color_btn():
    colors = _get_colors()
    return f"""
             QPushButton {{ 
                    background-color: {colors.blue}; 
                    color: #DFE1D7; 
                }}
             QPushButton:pressed {{ background-color: {colors.pressed_blue}; }}
             QPushButton:hover {{ background-color: {colors.hovered_blue}; }}
             QPushButton:selected {{ background-color: {colors.pressed_blue}; }}
             QPushButton:clicked {{ background-color: {colors.pressed_blue}; }}
         
            """

def zone_item_btn():
    colors = _get_colors()
    return f"""
             QPushButton {{ 
                    background-color: {colors.background_color}; 
                    color: #DFE1D7; 
                }}
             QPushButton:pressed {{ background-color: {colors.pressed_gray}; }}
             QPushButton:hover {{ background-color: {colors.hovered_blue}; }}
             QPushButton:clicked {{ background-color: {colors.pressed_blue}; }}
         
            """


def stop_realtime_btn_state1():
    colors = _get_colors()
    return f"""
            QPushButton {{ background-color: {colors.gray};}}
            QPushButton:hover {{background-color: {colors.hovered_gray};}}
            QPushButton:pressed {{background-color: {colors.pressed_gray};}} 
            """


def stop_realtime_btn_state2():
    colors = _get_colors()
    return f"""
            background-color: {colors.red};
            :hover {{background-color: {colors.hovered_red};}}
            :pressed {{background-color: {colors.pressed_red};}} 
           """


def button_style():
    return f'''
        QPushButton {{
            background-color: #333;
            border-radius: 10px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: #666;
        }}
        QPushButton:pressed {{
            background-color: #999;
        }}
    '''

# ...
