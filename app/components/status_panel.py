from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
import os

class StatusPanel(QWidget):
    """Always-visible status panel at the top center of the screen."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(650)  # Increased width for longer messages
        self.setFixedHeight(80)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        self.main_layout.setSpacing(5)
        
        # Title Layout (Horizontal - for logo + text)
        self.title_layout = QHBoxLayout()
        self.title_layout.setSpacing(10)
        
        # Logo/Image
        self.logo_label = QLabel()
        logo_path = os.path.join("app", "assests", "colored-logo-only.png")  # Adjust path as needed
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                32, 32, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)
        else:
            # Fallback emoji if image not found
            self.logo_label.setText("🤖")
            self.logo_label.setStyleSheet("font-size: 24px;")
        
        # Title Text
        self.title = QLabel("Nova Gaze AI")
        self.title.setStyleSheet("""
            color: #00d4ff; 
            font-weight: bold; 
            font-size: 18px;
            letter-spacing: 1px;
        """)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add logo and title to horizontal layout
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.logo_label)
        self.title_layout.addWidget(self.title)
        self.title_layout.addStretch()
        
        # Add title layout to main layout
        self.main_layout.addLayout(self.title_layout)
        
        # Status Label
        self.status_label = QLabel("Ready - Blink to activate")
        self.status_label.setStyleSheet("""
            color: #a0a0a0; 
            font-size: 14px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.status_label)

    def update_status(self, message):
        """Updates the status message."""
        self.status_label.setText(message)

    def paintEvent(self, event):
        """Custom paint for rounded, semi-transparent background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 15, 15, 230))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)