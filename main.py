import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab

class NovaGazeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set window to full screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)

        # Initialize and position the Tab in the Top-Middle
        self.top_tab = TopControlTab(self)
        tab_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        self.top_tab.move(tab_x, 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NovaGazeOverlay()
    window.show()
    sys.exit(app.exec())