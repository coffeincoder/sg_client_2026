# importing libraries
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from src.ui.style_sheets import *


# class for scrollable label
class ScrollLabel(QScrollArea):

    # constructor
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        # making widget resizable
        self.setWidgetResizable(True)


        # making qwidget object
        content = QWidget(self)
        self.setWidget(content)
        # vertical box layout
        lay = QVBoxLayout(content)

        # creating label
        self.label = QLabel(content)
        self.label.setWordWrap(True)

        # setting alignment to the text
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.label.setStyleSheet(scroll_label_list_item_text_style())
        self.setStyleSheet(scroll_label_list_item_style())
        # making label multi-line
        self.label.setWordWrap(True)

        # adding label to the layout
        lay.addWidget(self.label)

        # the setText method
    def setText(self, text):
        # setting text to the label
        self.label.setText(text)
