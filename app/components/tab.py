from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QLinearGradient

class TopControlTab(QWidget):
    # Create a custom signal so the Layout can listen for the close request
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 45)
        
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
        self.close_btn.clicked.connect(self.close_requested.emit)
        self.layout.addWidget(self.close_btn)

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