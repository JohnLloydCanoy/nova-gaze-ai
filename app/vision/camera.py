"""
Camera Module - Captures webcam feed and processes eye tracking
Uses MediaPipe-based eye_tracker.py for accurate blink detection
"""

import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

# Import the eye tracker
from app.logic.eye_tracker import EyeTracker


class CameraThread(QThread):
    """
    Thread that captures camera frames and processes eye tracking.
    Emits blink signals for manual navigation.
    """
    
    # Visual signals
    change_pixmap_signal = Signal(QImage)
    
    # Eye tracking signals
    gaze_signal = Signal(float, float, str)  # h_ratio, v_ratio, direction
    blink_signal = Signal(str)  # "BLINK", "DOUBLE_BLINK", "LONG_BLINK"
    calibration_signal = Signal(bool, float)  # is_calibrating, progress
    gaze_direction_signal = Signal(str)  # Simplified direction
    
    def __init__(self):
        super().__init__()
        self._run_flag = True
        
        # Initialize the eye tracker
        self.eye_tracker = EyeTracker()
        
        print("[CameraThread] ✅ Initialized with EyeTracker")
    
    def run(self):
        """Main camera capture and processing loop."""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[CameraThread] ❌ ERROR: Could not open camera")
            return
        
        print("[CameraThread] ✅ Camera opened successfully")
        
        while self._run_flag:
            ret, cv_img = cap.read()
            if not ret:
                continue
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            # Process frame with eye tracker
            tracking = self.eye_tracker.process_frame(rgb_frame)
            
            if tracking['face_detected']:
                # Emit blink signal (MOST IMPORTANT FOR NAVIGATION)
                if tracking['blink_event']:
                    self.blink_signal.emit(tracking['blink_event'])
                    print(f"[CameraThread] 👁️ {tracking['blink_event']} detected")
                
                # Emit other tracking data (for reference)
                self.gaze_signal.emit(
                    tracking['gaze_h'],
                    tracking['gaze_v'],
                    tracking['gaze_direction']
                )
                
                # Emit simplified direction
                direction = self._get_simple_direction(tracking['gaze_direction'])
                self.gaze_direction_signal.emit(direction)
                
                # Emit calibration status
                self.calibration_signal.emit(
                    tracking['calibrating'],
                    tracking['calibration_progress']
                )
            
            # Prepare image for display
            cv_img = cv2.flip(cv_img, 1)  # Mirror the image
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
            scaled_image = qt_image.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
            self.change_pixmap_signal.emit(scaled_image)
        
        cap.release()
        print("[CameraThread] ✅ Camera released")
    
    def _get_simple_direction(self, full_direction):
        """
        Convert full direction string to simple cardinal direction.
        E.g., "UP-LEFT" -> "up", "CENTER" -> "center"
        """
        if 'LEFT' in full_direction and 'UP' not in full_direction and 'DOWN' not in full_direction:
            return 'left'
        elif 'RIGHT' in full_direction and 'UP' not in full_direction and 'DOWN' not in full_direction:
            return 'right'
        elif 'UP' in full_direction and 'LEFT' not in full_direction and 'RIGHT' not in full_direction:
            return 'up'
        elif 'DOWN' in full_direction and 'LEFT' not in full_direction and 'RIGHT' not in full_direction:
            return 'down'
        else:
            return 'center'
    
    def stop(self):
        """Stop the camera thread."""
        self._run_flag = False
        self.wait()


class CameraFeedWidget(QWidget):
    """
    Widget that displays the camera feed with semi-transparency.
    Can be dragged around the screen.
    
    Forwards blink signals from CameraThread to the overlay.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 240)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)
        
        # Semi-transparent effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.4)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Dragging state
        self._drag_pos = None
        
        # Start camera thread
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
        
        print("[CameraFeedWidget] ✅ Initialized and started")
    
    def mousePressEvent(self, event):
        """Allow dragging the widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Stop dragging."""
        self._drag_pos = None
        event.accept()
    
    @Slot(QImage)
    def update_image(self, qt_image):
        """Update the displayed camera image."""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def closeEvent(self, event):
        """Stop the thread when the widget closes."""
        self.thread.stop()
        event.accept()