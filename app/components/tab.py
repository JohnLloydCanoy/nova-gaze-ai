import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap

class TopControlTab(QWidget):
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 50) # Reduced height since chat/input are removed
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        
        # --- Header ---
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(10)
        
        # Logo
        self.logo_label = QLabel()
        logo_path = os.path.join("app", "assests", "colored-logo-only.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        
        # Title
        self.title_label = QLabel(" Gaze AI")
        self.title_label.setStyleSheet("""
            font-weight: bold; 
            color: #BF00FF; 
            font-size: 15px;
            letter-spacing: 0.5px;
        """)
        
        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1); 
                color: #ff5555; 
                font-size: 16px; 
                border: none; 
                border-radius: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.2);
            }
        """)
        self.close_btn.clicked.connect(self.close_requested.emit)

        self.header_layout.addWidget(self.logo_label)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.close_btn)
        
        self.main_layout.addLayout(self.header_layout)

    def paintEvent(self, event):
        """Draws the rounded rectangular background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 15, 15, 230)) # Premium feel dark background
        painter.setPen(Qt.PenStyle.NoPen) 
        painter.drawRoundedRect(self.rect(), 18, 18)