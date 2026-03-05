import sys
from PySide6.QtWidgets import QApplication
from app.layout import NovaGazeOverlay

def main():
    app = QApplication(sys.argv)
    window = NovaGazeOverlay()