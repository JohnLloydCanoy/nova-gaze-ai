import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PySide6.QtGui import QScreen, QPixmap
from app.components.tab import TopControlTab
from app.vision.camera import CameraFeedWidget
from app.assistant.panel import AssistantPanel  # NEW

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
        """Initializes and positions all child UI components."""

        # Central widget + layout
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Camera Feed Widget (left side)
        self.camera_widget = CameraFeedWidget(self)
        main_layout.addWidget(self.camera_widget)

        # Add stretch to push the assistant panel to the far right
        main_layout.addStretch()  # NEW

        # Assistant Panel (right side)
        assistant_panel = AssistantPanel()
        main_layout.addWidget(assistant_panel)  # NEW

        # Top Control Tab (floating at top center)
        self.top_tab = TopControlTab(self)
        self.top_tab.close_requested.connect(QApplication.instance().quit)
        
        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        top_margin = 20
        self.top_tab.move(center_x, top_margin)
        self.top_tab.move(center_x, 20)
        self.top_tab.send_message_requested.connect(self.handle_ai_chat)
        
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
