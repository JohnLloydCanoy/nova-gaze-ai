import sys
import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QApplication, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal, Slot, QPoint
from PySide6.QtGui import QImage, QPixmap, QPainter, QPainterPath, QColor, QFont
from app.vision.gaze_tracker import GazeAnalyzer


class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage, str, float)
    
    gaze_action_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.gaze_analyzer = GazeAnalyzer()# Initialize the brain