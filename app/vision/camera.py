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
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class CameraFeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 240)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        # Apply 50% Opacity to the entire widget
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.5)
        self.setGraphicsEffect(self.opacity_effect)

        # Start the video thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    @Slot(QImage)
    def update_image(self, qt_image):
        """Updates the label with the newest camera frame"""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def shutdown(self):
        """Safely turns off the camera light when the app closes"""
        self.thread.stop()