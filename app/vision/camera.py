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
        
    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                cv_img = cv2.flip(cv_img, 1) # Mirror effect
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                
                processed_img, event, status_text, progress = self.gaze_analyzer.process_frame(rgb_image)
                
                if event:
                    self.gaze_action_signal.emit(event)
                    
                h, w, ch = processed_img.shape
                bytes_per_line = ch * w
                qt_image = QImage(processed_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                scaled_qt_image = qt_image.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
                
                # Emit the image and the UI data
                self.change_pixmap_signal.emit(scaled_qt_image, status_text, progress)
                
        cap.release()
        
    def stop(self):
        self._run_flag = False
        self.wait()
        
class RoundedCameraLabel(QLabel):
    def __init__(self, parent=None, radius=20):
        super().__init__(parent)
        self.radius = radius

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.radius, self.radius)
        painter.setClipPath(path)
        
        if self.pixmap():
            painter.drawPixmap(self.rect(), self.pixmap())
            
class CameraFeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 240)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Camera Feed
        self.image_label = RoundedCameraLabel(self, radius=20) 
        self.layout.addWidget(self.image_label)
        
        
        # --- NEW: Modern Gaze Status UI Overlay ---
        self.status_overlay = QWidget(self.image_label)
        self.status_overlay.setGeometry(0, 200, 320, 40)
        self.status_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(18, 18, 18, 0.7);
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
            }
        """)
        
        # Layout for the overlay
        self.overlay_layout = QHBoxLayout(self.status_overlay)
        self.overlay_layout.setContentsMargins(15, 0, 15, 0)
        
        # Text Label indicating current gaze
        self.gaze_label = QLabel("GAZE: INIT")
        self.gaze_label.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 14px; background: transparent;")
        self.overlay_layout.addWidget(self.gaze_label)