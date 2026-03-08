import cv2
import time
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from app.logic.eye_tracker import EyeTracker

class CameraThread(QThread):
    # Signals for video feed and eye tracking
    change_pixmap_signal = Signal(QImage)
    gaze_signal = Signal(float, float, str)     # h_ratio, v_ratio, direction
    gaze_direction_signal = Signal(str)         # direction only
    blink_signal = Signal(str)                  # "BLINK", "DOUBLE_BLINK", "LONG_BLINK"
    calibration_signal = Signal(bool, float)    # is_calibrating, progress

    # Signals expected by NovaGazeOverlay
    select_blink_signal = Signal()              # short blink (3s)
    close_blink_signal = Signal()               # long blink (6s)
    gaze_right_hold_signal = Signal()           # look right for 6s

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.eye_tracker = EyeTracker()
        self._right_hold_start = None

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                tracking = self.eye_tracker.process_frame(rgb_frame)

                if tracking['face_detected']:
                    # Emit gaze data
                    self.gaze_signal.emit(
                        tracking['gaze_h'],
                        tracking['gaze_v'],
                        tracking['gaze_direction']
                    )
                    self.gaze_direction_signal.emit(tracking['gaze_direction'])
                    self.calibration_signal.emit(
                        tracking['calibrating'],
                        tracking['calibration_progress']
                    )

                    # Blink events
                    if tracking['blink_event']:
                        self.blink_signal.emit(tracking['blink_event'])
                        if tracking['blink_event'] == "BLINK":
                            self.select_blink_signal.emit()
                        elif tracking['blink_event'] == "LONG_BLINK":
                            self.close_blink_signal.emit()

                    # Detect gaze right hold (6s)
                    if tracking['gaze_direction'] == "right":
                        if self._right_hold_start is None:
                            self._right_hold_start = time.time()
                        else:
                            if time.time() - self._right_hold_start >= 6:
                                self.gaze_right_hold_signal.emit()
                                self._right_hold_start = None
                    else:
                        self._right_hold_start = None

                # Convert to QImage for display
                cv_img = cv2.flip(cv_img, 1)
                height, width, channel = cv_img.shape
                bytes_per_line = 3 * width
                q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
                self.change_pixmap_signal.emit(q_img)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()


# --- CameraFeedWidget wrapper ---
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class CameraFeedWidget(QWidget):
    """
    A QWidget that displays the camera feed and forwards signals
    from CameraThread to the overlay.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Start camera thread
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)

        # Forward signals so NovaGazeOverlay can connect directly
        self.gaze_signal = self.thread.gaze_signal
        self.gaze_direction_signal = self.thread.gaze_direction_signal
        self.blink_signal = self.thread.blink_signal
        self.calibration_signal = self.thread.calibration_signal
        self.select_blink_signal = self.thread.select_blink_signal
        self.close_blink_signal = self.thread.close_blink_signal
        self.gaze_right_hold_signal = self.thread.gaze_right_hold_signal

        self.thread.start()

    def update_image(self, q_img):
        """Update the QLabel with the latest frame."""
        self.label.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        """Stop the thread when the widget closes."""
        self.thread.stop()
        event.accept()