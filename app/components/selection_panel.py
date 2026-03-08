from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter

class SelectionPanel(QWidget):
    option_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setFixedHeight(420)
        
        # Style the panel as a dark, semi-transparent overlay
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Look to Select")
        self.title.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 18px;")
        self.layout.addWidget(self.title)
        
        # Instructions
        self.instructions = QLabel("👁️ UP | LEFT | RIGHT\nClose eyes 3s to confirm")
        self.instructions.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.instructions)

        self.buttons = []
        labels = ["👆 Option 1", "👈 Option 2", "👉 Option 3"]
        for i, label in enumerate(labels):
            btn = QPushButton(f"{label}: Waiting...")
            btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a1a; color: white; border: 2px solid #333;
                    padding: 15px; border-radius: 10px; font-size: 14px;
                }
            """)
            self.layout.addWidget(btn)
            self.buttons.append(btn)

    def update_options(self, options):
        """Updates button text with AI suggestions."""
        labels = ["👆", "👈", "👉"]  # Up, Left, Right
        for i, text in enumerate(options):
            if i < len(self.buttons):
                self.buttons[i].setText(f"{labels[i]} {text}")

    def highlight_option(self, index):
        """Visual feedback for blink counting."""
        for i, btn in enumerate(self.buttons):
            if i == index - 1:
                btn.setStyleSheet("background: #00d4ff; color: black; padding: 15px; border-radius: 10px;")
            else:
                btn.setStyleSheet("background: #1a1a1a; color: white; padding: 15px; border-radius: 10px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(15, 15, 15, 230))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)