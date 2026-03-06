import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab
from app.vision.camera import CameraThread


class NovaGazeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        # Global Window Properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Make the window cover the entire screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self.setup_components(screen_geo)
        
    def setup_components(self, screen_geo):
        """Initializes and positions all child UI components."""
        self.top_tab = TopControlTab(self)
        self.top_tab.close_requested.connect(sys.exit)
        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        top_margin = 20
        
        self.top_tab.move(center_x, top_margin)