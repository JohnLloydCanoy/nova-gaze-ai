import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from app.components.tab import TopControlTab
from app.components.gaze_dot import GazeDot, CalibrationOverlay
from app.vision.camera import CameraFeedWidget


class NovaGazeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        # Global Window Properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Make the window cover the entire screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self._screen_width = screen_geo.width()
        self._screen_height = screen_geo.height()
        self.setup_components(screen_geo)
        
    def setup_components(self, screen_geo):
        """Initializes and positions all child UI components."""
        # Camera Feed Widget
        self.camera_widget = CameraFeedWidget(self)
        self.camera_widget.move(20, 20)
        
        # Gaze Dot - follows where user is looking
        self.gaze_dot = GazeDot(self, size=50)
        self.gaze_dot.move(screen_geo.width() // 2, screen_geo.height() // 2)
        
        # Calibration Overlay - shows during calibration
        self.calibration_overlay = CalibrationOverlay(self)
        self.calibration_overlay.setGeometry(0, 0, screen_geo.width(), screen_geo.height())
        self.calibration_overlay.show()
        
        # Connect eye tracking signals
        self.camera_widget.gaze_signal.connect(self.on_gaze)
        self.camera_widget.blink_signal.connect(self.on_blink)
        self.camera_widget.calibration_signal.connect(self.on_calibration)
        
        self.top_tab = TopControlTab(self)
        self.top_tab.close_requested.connect(sys.exit)
        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        top_margin = 20
        
        self.top_tab.move(center_x, top_margin)
    
    def on_gaze(self, h, v, direction):
        """Move gaze dot to follow eye gaze."""
        self.gaze_dot.set_gaze_position(h, v, self._screen_width, self._screen_height)
    
    def on_blink(self, event):
        """Handle blink events - pulse the gaze dot."""
        self.gaze_dot.pulse_on_blink()
        print(f"[BLINK] >>> {event} <<<")
    
    def on_calibration(self, is_calibrating, progress):
        """Handle calibration status - show/hide overlays."""
        self.gaze_dot.set_calibrating(is_calibrating)
        self.calibration_overlay.set_progress(progress)
        
        if not is_calibrating:
            self.calibration_overlay.hide()
            print("[CALIBRATION] Complete! Gaze dot now active.")
        