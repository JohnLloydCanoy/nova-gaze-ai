import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)
    def __init__(self):
        super().__init__()
        self._run_flag = True
    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                # Scale the image to fit the label while maintaining aspect ratio
                scaled_qt_image = qt_image.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(scaled_qt_image)
        cap.release()