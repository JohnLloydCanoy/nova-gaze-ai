import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont

class TopControlTab(QWidget):
    close_requested = Signal()
    send_message_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 250) # Slightly increased height for better spacing
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0) 

        # Label Component
        self.title_label = QLabel("Nova Gaze AI")
        self.title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #ffffff;
        """)
        self.layout.addWidget(self.title_label) 

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(spacer)

        # Close Button (red style)
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(130, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                color: #ffffff;
                background-color: rgba(220, 20, 60, 200); /* crimson red */
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 220); /* brighter red on hover */
            }
        """)

        # Connect to our internal signal instead of sys.exit directly
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 12, 15, 12)
        self.main_layout.setSpacing(8)

        # --- Refined Header ---
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(10)
        
        # Logo on the left side of the title
        self.logo_label = QLabel()
        logo_path = os.path.join("app", "assests", "colored-logo-only.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        
        self.title_label = QLabel(" Gaze AI")
        self.title_label.setStyleSheet("""
            font-weight: bold; 
            color: #BF00FF; 
            font-size: 15px;
            letter-spacing: 0.5px;
        """)
        
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

        # --- Chat Display with HTML Support ---
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background: rgba(25, 25, 25, 200); 
            color: #e0e0e0; 
            border: 1px solid #333; 
            border-radius: 8px;
            padding: 8px;
            line-height: 1.4;
        """)
        self.main_layout.addWidget(self.chat_display)

        # --- Input Area ---
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Nova...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a; 
                color: white; 
                border: 1px solid #00d4ff; 
                padding: 8px; 
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: #222;
            }
        """)
        self.chat_input.returnPressed.connect(self.process_input)
        self.main_layout.addWidget(self.chat_input)

        # Initial Welcome Message
        self.add_assistant_message("System ready. I can see your screen. How can I assist your navigation today?")

    def process_input(self):
        text = self.chat_input.text().strip()
        if text:
            self.add_user_message(text)
            self.chat_input.clear()
            self.send_message_requested.emit(text)

    def add_user_message(self, text):
        """Colorizes user messages in blue-cyan."""
        bubble = f'<div style="margin-bottom: 5px;"><b style="color: #00d4ff;">You:</b> <span style="color: #ffffff;">{text}</span></div>'
        self.chat_display.append(bubble)
        self.add_divider()

    def add_assistant_message(self, text):
        """Styles assistant messages in a neutral-soft tone."""
        bubble = f'<div style="margin-bottom: 5px;"><b style="color: #a0a0a0;">Nova:</b> <span style="color: #e0e0e0;">{text}</span></div>'
        self.chat_display.append(bubble)
        self.add_divider()

    def add_divider(self):
        """Adds a subtle horizontal line divider."""
        divider = '<hr style="border: 0; height: 1px; background: #333; margin: 5px 0;">'
        self.chat_display.append(divider)
        self.chat_display.ensureCursorVisible()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient semi-transparent background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(30, 30, 30, 180))
        gradient.setColorAt(1, QColor(50, 50, 50, 180))

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.setBrush(QColor(15, 15, 15, 230)) # Slightly darker for premium feel
        painter.setPen(Qt.PenStyle.NoPen) 
        painter.drawRoundedRect(self.rect(), 18, 18)
