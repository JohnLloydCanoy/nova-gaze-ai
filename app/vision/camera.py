import sys
import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QApplication
from PySide6.QtCore import Qt, QThread, Signal, Slot, QPoint
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

        # 1. Make the window frameless and ensure it stays on top of other windows
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        # Apply 40% Opacity to the entire widget
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.4)
        self.setGraphicsEffect(self.opacity_effect)

        # Track the mouse position for dragging
        self._drag_pos = None

        # Start the video thread
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    # --- 2. Mouse Events to enable dragging ---
    def mousePressEvent(self, event):
        """Triggered when the user clicks the widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the distance between the mouse click and the top-left corner of the window
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Triggered when the user drags the mouse."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            # Move the window to the new mouse position, minus the initial offset
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Triggered when the user releases the mouse button."""
        self._drag_pos = None
        event.accept()
    # ------------------------------------------

    @Slot(QImage)
    def update_image(self, qt_image):
        """Updates the label with the newest camera frame"""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def shutdown(self):
        """Safely turns off the camera light when the app closes"""
        self.thread.stop()


# --- Execution Block to test the app ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = CameraFeedWidget()
    widget.show()
    
    # Catch the application exit to ensure the camera shuts down cleanly
    app.aboutToQuit.connect(widget.shutdown)
    
    sys.exit(app.exec())