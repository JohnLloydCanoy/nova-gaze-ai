from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab

class NovaGazeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()