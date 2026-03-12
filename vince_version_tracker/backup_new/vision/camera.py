import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from app.logic.eye_tracker import EyeTracker

class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)
    # New signals to match the eye_tracker logic
    gaze_signal = Signal(float, float, str)     # h_ratio, v_ratio, direction
    blink_signal = Signal(str)                  # "BLINK", "DOUBLE_BLINK", etc.
    calibration_signal = Signal(bool, float)    # is_calibrating, progress
    
    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.eye_tracker = EyeTracker() 
        
    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # 1. Process tracking
                rgb_frame = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                tracking = self.eye_tracker.process_frame(rgb_frame)
                
                if tracking['face_detected']:
                    # 2. Emit tracking data
                    self.gaze_signal.emit(
                        tracking['gaze_h'], 
                        tracking['gaze_'], 
                        tracking['gaze_direction']
                    )
                        
                    self.calibration_signal.emit(
                        tracking['calibrating'], 
                        tracking['calibration_progress']
                    )

                    if tracking['blink_event']:
                        self.blink_signal.emit(tracking['blink_event'])

                # 3. Convert to QImage for display
                cv_img = cv2.flip(cv_img, 1)
                height, width, channel = cv_img.shape
                bytes_per_line = 3 * width
                q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
                self.change_pixmap_signal.emit(q_img)
                
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()