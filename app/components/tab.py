import sys
# 1. Import QLabel along with the other widgets
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor

class TopControlTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(500, 45)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0) 
        
        # TEXT LABEL ON THE LEFT
        self.title_label = QLabel("HELLO WORLD")
        self.title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            letter-spacing: 1px;
        """)
        self.layout.addWidget(self.title_label) 

        # The spacer comes AFTER the label, pushing the Close button to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(spacer)

        self.close_btn = QPushButton("✕ Close Program")
        self.close_btn.setFixedSize(130, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 50, 50, 220);
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 255);
            }
        """)
        
        self.close_btn.clicked.connect(sys.exit)
        self.layout.addWidget(self.close_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(0, 0, 0, 128)) 
        painter.setPen(Qt.PenStyle.NoPen) 
        
        rect = self.rect()
        # Changed to 10, 10 to round ALL four corners so it looks good floating
        painter.drawRoundedRect(rect, 10, 10)