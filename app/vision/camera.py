import cv2
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, Signal, Slot, QPoint
from PySide6.QtGui import QImage, QPixmap
from app.logic.tracker import GazeTracker

class CameraThread(QThread):
    change_pixmap_signal = Signal(QImage)
    blink_signal = Signal(bool)
    select_blink_signal = Signal()  # Emitted when 3-second blink is detected
    close_blink_signal = Signal()   # Emitted when 6-second blink is detected
    gaze_direction_signal = Signal(str)  # 'left', 'right', 'up', 'down', 'center'
    gaze_right_hold_signal = Signal()  # Emitted when looking RIGHT for 6 seconds
    
    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.tracker = GazeTracker()
        self.blink_counter = 0
        self.select_emitted = False
        self.close_emitted = False
        
        # Gaze hold tracking for RIGHT direction
        self.gaze_right_counter = 0
        self.gaze_right_hold_emitted = False
        self.GAZE_RIGHT_THRESHOLD = 180  # ~6 seconds at 30fps

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                _, is_blinking, gaze_direction, horizontal_gaze = self.tracker.process_frame(cv_img)
                
                # Track blink duration
                if is_blinking:
                    self.blink_counter += 1
                    
                    # 3-second blink for selection
                    if self.blink_counter >= self.tracker.SELECT_BLINK_THRESHOLD and not self.select_emitted:
                        self.select_blink_signal.emit()
                        self.select_emitted = True
                    
                    # 6-second blink to close system
                    if self.blink_counter >= self.tracker.CLOSE_BLINK_THRESHOLD and not self.close_emitted:
                        self.close_blink_signal.emit()
                        self.close_emitted = True
                else:
                    # Reset counters when eyes open
                    self.blink_counter = 0
                    self.select_emitted = False
                    self.close_emitted = False
                
                # Track looking RIGHT for 6 seconds
                if horizontal_gaze > 0.70:  # Looking strongly right
                    self.gaze_right_counter += 1
                    if self.gaze_right_counter >= self.GAZE_RIGHT_THRESHOLD and not self.gaze_right_hold_emitted:
                        self.gaze_right_hold_signal.emit()
                        self.gaze_right_hold_emitted = True
                else:
                    self.gaze_right_counter = 0
                    self.gaze_right_hold_emitted = False
                
                self.blink_signal.emit(is_blinking)
                if gaze_direction:
                    self.gaze_direction_signal.emit(gaze_direction)
                
                cv_img = cv2.flip(cv_img, 1)
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
                scaled_image = qt_image.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
                self.change_pixmap_signal.emit(scaled_image)
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class CameraFeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 240)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.4)
        self.setGraphicsEffect(self.opacity_effect)

        self._drag_pos = None # Track mouse for dragging
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    @Slot(QImage)
    def update_image(self, qt_image):
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))