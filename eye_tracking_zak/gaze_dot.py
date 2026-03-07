"""
Gaze Dot Component - Visual cursor that follows eye gaze.
Shows where the user is looking on screen.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient


class GazeDot(QWidget):
    """
    A visual gaze indicator that moves smoothly to follow eye gaze.
    
    Features:
    - Smooth animation between positions
    - Visual feedback for blinks (pulse effect)
    - Calibration indicator mode
    - Configurable appearance
    """
    
    def __init__(self, parent=None, size=40):
        super().__init__(parent)
        self.dot_size = size
        self.setFixedSize(size, size)
        
        # Make it click-through (doesn't intercept mouse events)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Visual state
        self._opacity = 0.8
        self._color = QColor(0, 200, 255)  # Cyan
        self._pulse_scale = 1.0
        self._is_calibrating = True
        
        # Smoothing - store target position
        self._target_x = 0
        self._target_y = 0
        self._current_x = 0.0
        self._current_y = 0.0
        self._smoothing = 0.15  # Lower = smoother but more lag
        
        # Animation for blink pulse
        self._setup_animations()
        
        # Start hidden until calibration completes
        self.hide()
    
    def _setup_animations(self):
        """Setup pulse animation for blinks."""
        self._pulse_anim = QPropertyAnimation(self, b"pulse_scale")
        self._pulse_anim.setDuration(200)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    # Property for pulse animation
    def get_pulse_scale(self):
        return self._pulse_scale
    
    def set_pulse_scale(self, value):
        self._pulse_scale = value
        self.update()
    
    pulse_scale = Property(float, get_pulse_scale, set_pulse_scale)
    
    def set_gaze_position(self, h_ratio, v_ratio, screen_width, screen_height):
        """
        Update the target gaze position.
        
        Args:
            h_ratio: Horizontal gaze ratio (0=left, 0.5=center, 1=right)
            v_ratio: Vertical gaze ratio (0=up, 0.5=center, 1=down)
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        # Convert ratios to screen coordinates
        self._target_x = int(h_ratio * screen_width) - self.dot_size // 2
        self._target_y = int(v_ratio * screen_height) - self.dot_size // 2
        
        # Apply smoothing (exponential moving average)
        self._current_x += (self._target_x - self._current_x) * self._smoothing
        self._current_y += (self._target_y - self._current_y) * self._smoothing
        
        # Move the widget
        self.move(int(self._current_x), int(self._current_y))
    
    def pulse_on_blink(self):
        """Trigger a pulse animation when user blinks."""
        self._pulse_anim.stop()
        self._pulse_anim.setStartValue(1.5)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.start()
    
    def set_calibrating(self, is_calibrating):
        """Show/hide based on calibration state."""
        self._is_calibrating = is_calibrating
        if is_calibrating:
            self.hide()
        else:
            self.show()
    
    def set_color(self, color):
        """Set the dot color."""
        self._color = color
        self.update()
    
    def set_smoothing(self, value):
        """Set smoothing factor (0.05-0.5). Lower = smoother but more lag."""
        self._smoothing = max(0.05, min(0.5, value))
    
    def paintEvent(self, event):
        """Draw the gaze dot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate size with pulse effect
        size = int(self.dot_size * self._pulse_scale)
        offset = (self.dot_size - size) // 2
        
        # Create gradient for nice visual
        center_x = self.dot_size // 2
        center_y = self.dot_size // 2
        
        gradient = QRadialGradient(center_x, center_y, size // 2)
        
        # Inner color (brighter)
        inner_color = QColor(self._color)
        inner_color.setAlpha(int(255 * self._opacity))
        
        # Outer color (fades out)
        outer_color = QColor(self._color)
        outer_color.setAlpha(int(100 * self._opacity))
        
        gradient.setColorAt(0, inner_color)
        gradient.setColorAt(0.5, inner_color)
        gradient.setColorAt(1, outer_color)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw outer glow
        painter.drawEllipse(offset, offset, size, size)
        
        # Draw inner dot (solid center)
        inner_size = size // 3
        inner_offset = (self.dot_size - inner_size) // 2
        painter.setBrush(QColor(255, 255, 255, int(200 * self._opacity)))
        painter.drawEllipse(inner_offset, inner_offset, inner_size, inner_size)


class CalibrationOverlay(QWidget):
    """
    Shows calibration instructions on screen.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._progress = 0.0
        self._visible = True
    
    def set_progress(self, progress):
        """Update calibration progress (0-1)."""
        self._progress = progress
        self.update()
    
    def set_visible_state(self, visible):
        """Show or hide the calibration overlay."""
        self._visible = visible
        if visible:
            self.show()
        else:
            self.hide()
    
    def paintEvent(self, event):
        """Draw calibration instructions."""
        if not self._visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Semi-transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Center text
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw "CALIBRATING" text
        painter.setPen(QColor(0, 255, 255))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(center_x - 100, center_y - 40, "CALIBRATING...")
        
        # Draw instruction
        font.setPointSize(14)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(center_x - 120, center_y, "Look straight at the camera")
        
        # Draw progress bar
        bar_width = 200
        bar_height = 10
        bar_x = center_x - bar_width // 2
        bar_y = center_y + 30
        
        # Background
        painter.fillRect(bar_x, bar_y, bar_width, bar_height, QColor(50, 50, 50))
        
        # Progress
        progress_width = int(bar_width * self._progress)
        painter.fillRect(bar_x, bar_y, progress_width, bar_height, QColor(0, 255, 255))
        
        # Border
        painter.setPen(QColor(100, 100, 100))
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
