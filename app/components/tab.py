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
    def on_suggestion_clicked(self, suggestion_text):
        self.add_user_message(f"Selected: {suggestion_text}")
        # Logic to execute the action goes here
    def add_divider(self):
        """Adds a subtle horizontal line divider."""
        divider = '<hr style="border: 0; height: 1px; background: #333; margin: 5px 0;">'
        self.chat_display.append(divider)
        self.chat_display.ensureCursorVisible()
    def add_suggestion_buttons(self, suggestions):
        """Adds interactive buttons for AI suggestions."""
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        for text in suggestions:
            btn = QPushButton(f"💡 {text}")
            btn.setStyleSheet("""
                QPushButton {
                    background: #2a2a2a; color: #00d4ff; text-align: left;
                    padding: 8px; border: 1px solid #333; border-radius: 4px;
                }
                QPushButton:hover { background: #333; border-color: #00d4ff; }
            """)
            # Connect button to an action (e.g., repeating it to the AI)
            btn.clicked.connect(lambda checked, t=text: self.on_suggestion_clicked(t))
            layout.addWidget(btn)

        # Append the entire button group to the chat display
        self.main_layout.insertWidget(self.main_layout.count() - 1, container)
        self.add_divider()
    def paintEvent(self, event):
        """Draws the rounded rectangular background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 15, 15, 230)) # Premium feel dark background
        painter.setPen(Qt.PenStyle.NoPen) 
        painter.drawRoundedRect(self.rect(), 18, 18)