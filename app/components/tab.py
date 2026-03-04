from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class TopControlTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(200, 40)
        self.setStyleSheet("""
            background-color: rgba(40, 40, 40, 128); /* 50% Opacity Black */
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """)