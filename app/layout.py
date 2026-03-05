from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab

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