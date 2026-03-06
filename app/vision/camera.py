import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)
    def __init__(self):
        super().__init__()
        self._run_flag = True