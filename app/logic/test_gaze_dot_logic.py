import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import Qt, Slot
from app.vision.camera import CameraThread
from app.components.gaze_dot import GazeDot, CalibrationOverlay

class LogicTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova-Gaze Pipeline Test")
        self.showFullScreen() 
        
        # Central widget (transparent)
        self.setCentralWidget(QWidget())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 1. Initialize Visual Components
        self.gaze_dot = GazeDot(self)
        self.calibration_ui = CalibrationOverlay(self)
        
        # 2. Initialize Camera/Logic Thread
        self.cam_thread = CameraThread()
        
        # 3. Link Logic to Visuals
        self.cam_thread.gaze_signal.connect(self.on_gaze)
        self.cam_thread.blink_signal.connect(self.on_blink)
        # FIXED: Removed the messy code inside the parentheses
        self.cam_thread.calibration_signal.connect(self.on_calibration)
        
        self.cam_thread.start()

    @Slot(float, float, str)
    def on_gaze(self, h, v, direction):
        screen = self.screen().size()
        # Corrected: Mapping ratios to screen pixels
        self.gaze_dot.set_gaze_position(h, v, screen.width(), screen.height())

    @Slot(str)
    def on_blink(self, event_type):
        print(f"Action Triggered: {event_type}")
        # FIXED: GazeDot uses pulse_on_blink(), not pulse()
        self.gaze_dot.pulse_on_blink() 

    @Slot(bool, float)
    def on_calibration(self, active, progress):
        self.calibration_ui.set_progress(progress)
        # FIXED: GazeDot uses set_calibrating() to handle its own visibility
        self.calibration_ui.set_visible_state(active)
        self.gaze_dot.set_calibrating(active)

    def closeEvent(self, event):
        self.cam_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogicTestWindow()
    window.show()
    sys.exit(app.exec())