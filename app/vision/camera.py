import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

# Import the eye tracker
from app.logic.eye_tracker import EyeTracker


class CameraThread(QThread):
    """
    Camera thread that captures video and processes eye tracking.
    
    Signals:
        change_pixmap_signal: Emits QImage for display
        gaze_signal: Emits (gaze_h, gaze_v, direction) - floats 0-1 and string
        blink_signal: Emits event string ("BLINK", "DOUBLE_BLINK", "LONG_BLINK")
        calibration_signal: Emits (is_calibrating, progress) - bool and float 0-1
        tracking_data_signal: Emits full tracking dict for advanced use
    """
    change_pixmap_signal = Signal(QImage)
    gaze_signal = Signal(float, float, str)  # gaze_h, gaze_v, direction
    blink_signal = Signal(str)  # "BLINK", "DOUBLE_BLINK", "LONG_BLINK"
    calibration_signal = Signal(bool, float)  # is_calibrating, progress
    tracking_data_signal = Signal(dict)  # Full tracking data
    
    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.eye_tracker = EyeTracker()
        self._last_calibrating = True
        
    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Flip for mirror effect
                cv_img = cv2.flip(cv_img, 1)
                
                # Convert to RGB for both display and tracking
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                
                # Process eye tracking
                tracking = self.eye_tracker.process_frame(rgb_image)
                
                # Emit tracking signals
                if tracking['face_detected']:
                    # Emit gaze data
                    self.gaze_signal.emit(
                        tracking['gaze_h'],
                        tracking['gaze_v'],
                        tracking['gaze_direction']
                    )
                    
                    # Emit blink events
                    if tracking['blink_event']:
                        self.blink_signal.emit(tracking['blink_event'])
                    
                    # Emit calibration status (only when it changes)
                    if tracking['calibrating'] != self._last_calibrating:
                        self.calibration_signal.emit(
                            tracking['calibrating'],
                            tracking['calibration_progress']
                        )
                        self._last_calibrating = tracking['calibrating']
                    elif tracking['calibrating']:
                        # Still calibrating, emit progress
                        self.calibration_signal.emit(True, tracking['calibration_progress'])
                
                # Emit full tracking data for advanced use
                self.tracking_data_signal.emit(tracking)
                
                # Create QImage for display
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                scaled_qt_image = qt_image.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(scaled_qt_image)
                
        cap.release()
        
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
    
    def reset_calibration(self):
        """Reset eye tracker calibration."""
        self.eye_tracker.reset_calibration()

class CameraFeedWidget(QWidget):
    """
    Widget that displays the camera feed with optional eye tracking overlay.
    
    Signals from the camera thread are exposed for other widgets to connect to:
        - gaze_signal(float, float, str): gaze_h, gaze_v, direction
        - blink_signal(str): "BLINK", "DOUBLE_BLINK", "LONG_BLINK"
        - calibration_signal(bool, float): is_calibrating, progress
    """
    
    # Re-expose signals from the thread for easy access
    gaze_signal = Signal(float, float, str)
    blink_signal = Signal(str)
    calibration_signal = Signal(bool, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 240)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        # Apply 40% Opacity to the entire widget
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.4)
        self.setGraphicsEffect(self.opacity_effect)

        # Start the video thread
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        
        # Forward signals from thread to widget level
        self.thread.gaze_signal.connect(self._forward_gaze)
        self.thread.blink_signal.connect(self._forward_blink)
        self.thread.calibration_signal.connect(self._forward_calibration)
        
        self.thread.start()

    def _forward_gaze(self, h, v, direction):
        self.gaze_signal.emit(h, v, direction)
    
    def _forward_blink(self, event):
        self.blink_signal.emit(event)
    
    def _forward_calibration(self, calibrating, progress):
        self.calibration_signal.emit(calibrating, progress)

    @Slot(QImage)
    def update_image(self, qt_image):
        """Updates the label with the newest camera frame"""
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def shutdown(self):
        """Safely turns off the camera light when the app closes"""
        self.thread.stop()
    
    def reset_calibration(self):
        """Reset eye tracking calibration."""
        self.thread.reset_calibration()