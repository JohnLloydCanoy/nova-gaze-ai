import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QBuffer, QIODevice, Signal
from PySide6.QtGui import QScreen, QPixmap
from app.components.tab import TopControlTab
from app.vision.camera import CameraFeedWidget
from app.assistant.sidepannel import ChatSidePanel


class NovaGazeOverlay(QMainWindow):
    def __init__(self, ai_client):
        super().__init__()
        self.nova = ai_client
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
        self.camera_widget = CameraFeedWidget(self)
        self.camera_widget.move(20, 20)
        
        self.top_tab = TopControlTab(self)
        self.top_tab.close_requested.connect(QApplication.instance().quit)
        
        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        self.top_tab.move(center_x, 20)
        
        # --- NEW: Add and position the Side Panel ---
        self.side_panel = ChatSidePanel(self)
        
        # Calculate X to snap to the right edge with a 20px margin
        panel_x = screen_geo.width() - self.side_panel.width() - 20
        # Calculate Y to center it vertically on the screen
        panel_y = (screen_geo.height() - self.side_panel.height()) // 2
        
        self.side_panel.move(panel_x, panel_y)
        
        # Wire the panel's chat input to your AI handler
        self.side_panel.send_message_requested.connect(self.handle_ai_chat)

    def handle_ai_chat(self, text):
        # Briefly hide to capture the clean desktop view
        self.hide()
        QApplication.processEvents()
        
        image_bytes = self.capture_screen()
        
        self.show()
        
        # Send to Nova client
        reply = self.nova.chat_with_vision(text, image_bytes)
        
        # --- UPDATED: Print the AI's reply directly into the new side panel ---
        formatted_reply = f'<br><span style="color: #BB86FC;"><b>Nova:</b></span> {reply}<br>'
        self.side_panel.chat_display.append(formatted_reply)
        
    def capture_screen(self):
        """Captures the current screen to show Nova."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        # Convert to bytes for OpenAI client
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        screenshot.save(buffer, "PNG")
        return buffer.data().data()

    def handle_ai_chat(self, text):
        # Briefly hide to capture the clean desktop view
        self.hide()
        QApplication.processEvents()
        
        image_bytes = self.capture_screen()
        
        self.show()
        
        # Send to Nova client
        reply = self.nova.chat_with_vision(text, image_bytes)
        
        # Use the new styled assistant message method
        self.top_tab.add_assistant_message(reply)