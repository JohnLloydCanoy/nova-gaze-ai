import sys
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor

class TopControlTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fixed width of 500px (~5 inches on standard displays) and 45px tall
        self.setFixedSize(500, 45)
        
        # 1. Setup Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 10, 0) # Left, Top, Right, Bottom padding
        
        # 2. Add an invisible "Spacer" that expands to push everything else to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(spacer)

        # 3. Create and style the Close Button
        self.close_btn = QPushButton("✕ Close Program")
        self.close_btn.setFixedSize(130, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor) # Shows a hand cursor on hover
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
        
        # Safely close the application when clicked
        self.close_btn.clicked.connect(sys.exit)
        self.layout.addWidget(self.close_btn)

    def paintEvent(self, event):
        """Draws the 50% opacity black background manually."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Color: Black (0, 0, 0). Alpha: 128 (out of 255, which is exactly 50% opacity)
        painter.setBrush(QColor(0, 0, 0, 128)) 
        painter.setPen(Qt.PenStyle.NoPen) # Removes the default outline
        
        # Draw the rectangle with slightly rounded bottom corners for a polished look
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)