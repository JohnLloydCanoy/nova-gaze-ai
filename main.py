import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab

class NovaGazeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Make the main window completely transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Make the window cover the entire screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self.top_tab = TopControlTab(self)
        
        # Calculate exactly center-top
        # Formula: (Screen Width / 2) - (Tab Width / 2)
        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        
        # ---> THIS IS THE NEW PART <---
        # Define the top margin (e.g., 20 pixels down from the top)
        top_margin = 20
        
        # Move the tab to X: center, Y: top_margin 
        self.top_tab.move(center_x, top_margin)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NovaGazeOverlay()
    window.show()
    sys.exit(app.exec())