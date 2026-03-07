import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QBuffer, QIODevice, QTimer
from app.vision.camera import CameraFeedWidget
from app.components.selection_panel import SelectionPanel
from app.components.status_panel import StatusPanel

class NovaGazeOverlay(QMainWindow):
    def __init__(self, ai_client):
        super().__init__()
        self.nova = ai_client
        self.is_processing = False
        
        # Navigation State
        self.current_direction = 'center'
        
        # AI Mode State
        self.ai_mode_active = False
        self.selected_option = 0
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self.setup_components(screen_geo)
        
    def setup_components(self, screen_geo):
        # Camera Widget
        self.camera_widget = CameraFeedWidget(self)
        self.camera_widget.move(20, 20)
        
        # Connect signals
        self.camera_widget.thread.select_blink_signal.connect(self.handle_select_blink)
        self.camera_widget.thread.close_blink_signal.connect(self.handle_close_blink)
        self.camera_widget.thread.gaze_direction_signal.connect(self.handle_gaze_direction)
        self.camera_widget.thread.gaze_right_hold_signal.connect(self.handle_gaze_right_close)
        
        # Status Panel (Top Center - Always Visible)
        self.status_panel = StatusPanel(self)
        center_x = (screen_geo.width() // 2) - (self.status_panel.width() // 2)
        self.status_panel.move(center_x, 20)
        self.status_panel.update_status("👁️ Look around | Close eyes 3s to Ask AI | Look RIGHT 6s or Close eyes 6s to Exit")
        self.status_panel.show()
        
        # Selection Panel (Right Side - Initially Hidden)
        self.selection_panel = SelectionPanel(self)
        self.selection_panel.move(screen_geo.width() - 320, (screen_geo.height() // 2) - 200)
        self.selection_panel.hide()

    def handle_gaze_direction(self, direction):
        """Handle eye gaze direction for navigation."""
        self.current_direction = direction
        
        if self.ai_mode_active:
            # In AI mode: Use gaze to select options
            self.handle_ai_selection(direction)
        else:
            # Normal mode: Just show where user is looking
            direction_emoji = {
                'left': '👈',
                'right': '👉',
                'up': '👆',
                'down': '👇',
                'center': '👁️'
            }
            
            # Special message for looking right
            if direction == 'right':
                self.status_panel.update_status(
                    f"{direction_emoji.get(direction, '👁️')} Looking RIGHT (hold 6s to exit) | "
                    f"Close eyes: 3s = Ask AI"
                )
            else:
                self.status_panel.update_status(
                    f"{direction_emoji.get(direction, '👁️')} Looking {direction.upper()} | "
                    f"Close eyes: 3s = Ask AI | Look RIGHT 6s = Exit"
                )
    
    def handle_ai_selection(self, direction):
        """Handle gaze-based selection in AI mode."""
        # Map gaze to options: up=1, left=2, right=3
        option_map = {'up': 1, 'left': 2, 'right': 3}
        current_option = option_map.get(direction, 0)
        
        if current_option > 0 and current_option <= 3:
            self.selected_option = current_option
            self.selection_panel.highlight_option(current_option)
    
    def handle_select_blink(self):
        """Handle 3-second blink - Activate AI or Select option."""
        if not self.is_processing:
            if not self.ai_mode_active:
                # Activate AI mode
                print("3-second blink detected! Activating AI...")
                self.activate_ai_mode()
            else:
                # In AI mode: Execute selected option
                if self.selected_option > 0:
                    print(f"3-second blink - Executing option {self.selected_option}")
                    self.execute_ai_selection()
                else:
                    print("No option selected. Please look at an option first.")
    
    def handle_close_blink(self):
        """Handle 6-second blink - Close the system."""
        print("6-second blink detected! Closing system...")
        self.close_system()
    
    def handle_gaze_right_close(self):
        """Handle looking RIGHT for 6 seconds - Close the system."""
        print("Looking RIGHT for 6 seconds! Closing system...")
        self.close_system()
    
    def close_system(self):
        """Close the entire system including terminal."""
        self.status_panel.update_status("👋 Closing system...")
        self.selection_panel.hide()
        
        # Stop camera thread
        if hasattr(self.camera_widget, 'thread'):
            self.camera_widget.thread.stop()
        
        # Close after 1 second and exit completely
        QTimer.singleShot(1000, self.force_close)
    
    def force_close(self):
        """Force close the application and exit Python."""
        import sys
        QApplication.quit()
        sys.exit(0)
    
    def activate_ai_mode(self):
        """Activate AI analysis mode."""
        self.is_processing = True
        self.status_panel.update_status("🔍 Analyzing screen...")
        
        # Capture screen
        self.hide() 
        QApplication.processEvents()
        image_bytes = self.capture_screen()
        self.show()
        
        # Get AI suggestions
        prompt = "Provide exactly 3 short numbered navigation actions based on what you see on screen."
        reply = self.nova.chat_with_vision(prompt, image_bytes)
        
        # Debug: Print AI response
        print(f"AI Response: {reply}")
        
        # Parse suggestions
        suggestions = [s.strip() for s in reply.split('\n') if s.strip() and any(char.isdigit() for char in s[:3])][:3]
        
        # Ensure we have 3 suggestions
        while len(suggestions) < 3:
            suggestions.append(f"Action {len(suggestions) + 1}")
        
        print(f"Parsed suggestions: {suggestions}")
        
        # Show selection panel
        self.selection_panel.update_options(suggestions)
        self.selection_panel.show()
        
        self.status_panel.update_status("👁️ Look UP/LEFT/RIGHT | Close eyes 3s to select | Look RIGHT 6s to close")
        self.ai_mode_active = True
        self.is_processing = False
        print("AI mode active. Look at option and close eyes for 3s to select.")
    
    def execute_ai_selection(self):
        """Execute the selected AI option."""
        if self.selected_option >= 1 and self.selected_option <= 3:
            print(f"✅ Executing Option {self.selected_option}")
            self.status_panel.update_status(f"✅ Executed Option {self.selected_option}")
        
        # Exit AI mode
        self.selection_panel.hide()
        self.ai_mode_active = False
        self.selected_option = 0
        
        # Reset status after 2 seconds
        QTimer.singleShot(2000, self.reset_to_normal_mode)
    
    def reset_to_normal_mode(self):
        """Reset back to normal navigation mode."""
        self.status_panel.update_status("👁️ Look around | Close eyes 3s to Ask AI | Look RIGHT 6s to Exit")

    def capture_screen(self):
        """Captures the current screen as image bytes."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        screenshot.save(buffer, "PNG")
        return buffer.data().data()