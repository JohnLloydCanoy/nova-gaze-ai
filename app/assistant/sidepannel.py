import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PySide6.QtGui import QScreen, QPixmap

from app.components.tab import TopControlTab
from app.vision.camera import CameraFeedWidget
from app.assistant.sidepannel import ChatSidePanel
from app.logic.process.procedure import execute_screen_analysis_procedure  # NEW: Import the orchestrator

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
        
        self.side_panel = ChatSidePanel(self)
        
        # Calculate X to snap to the right edge with a 20px margin
        panel_x = screen_geo.width() - self.side_panel.width() - 20
        # Calculate Y to center it vertically on the screen
        panel_y = (screen_geo.height() - self.side_panel.height()) // 2
        self.side_panel.move(panel_x, panel_y)
        
        # --- THE WIRING ---
        # 1. Wire the panel's chat input to the AI handler
        self.side_panel.send_message_requested.connect(self.handle_ai_chat)
        # 2. Wire the dynamic button clicks to the action handler
        self.side_panel.action_selected.connect(self.handle_button_click)

    def handle_ai_chat(self, text):
        """Routes the user's input to either the UI scanner or the standard chatbot."""
        text_lower = text.lower()
        
        # --- SCENARIO A: The user wants to scan the screen for buttons ---
        if "scan" in text_lower or "look" in text_lower:
            self.side_panel.chat_display.append('<span style="color: #BB86FC;"><b>Nova:</b> Scanning your screen, please wait...</span>')
            
            # Briefly hide the overlay to get a clean desktop screenshot
            self.hide()
            QApplication.processEvents()
            
            try:
                # Trigger the procedure we built earlier
                real_ai_data = execute_screen_analysis_procedure(self.nova)
            finally:
                # Always restore the UI
                self.show()
                QApplication.processEvents()
                
            # Populate the dynamic buttons
            if real_ai_data:
                self.side_panel.chat_display.append(f'<span style="color: #03DAC6;"><b>Nova:</b> Found {len(real_ai_data)} actions. What should we do?</span>')
                self.side_panel.generate_action_buttons(real_ai_data)
            else:
                self.side_panel.chat_display.append('<span style="color: #FF5252;"><b>Nova:</b> I could not identify any clear interactions on the screen.</span>')

        # --- SCENARIO B: Standard chat conversation ---
        else:
            self.hide()
            QApplication.processEvents()
            
            image_bytes = self.capture_screen()
            
            self.show()
            QApplication.processEvents()
            
            # Send to Nova client
            reply = self.nova.chat_with_vision(text, image_bytes)
            
            # Print the AI's reply into the side panel
            formatted_reply = f'<br><span style="color: #BB86FC;"><b>Nova:</b></span> {reply}<br>'
            self.side_panel.chat_display.append(formatted_reply)
            
            # Keep top tab updated as well (from your original code)
            if hasattr(self.top_tab, 'add_assistant_message'):
                self.top_tab.add_assistant_message(reply)

    def handle_button_click(self, action_data: dict):
        """Catches the emitted data when a user clicks a dynamically generated button."""
        action = action_data.get('action', 'Unknown Action')
        element = action_data.get('element_name', 'Unknown Element')
        
        # Acknowledge the click in the UI
        self.side_panel.chat_display.append(f'<span style="color: #03DAC6;"><b>System:</b> Preparing to execute {action} on {element}.</span>')
        
        # Next step: Move the mouse here!
        # self.move_mouse_to_element(element)
    def capture_screen(self):
        """Captures the current screen to show Nova (in-memory buffer for standard chat)."""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        screenshot.save(buffer, "PNG")
        return buffer.data().data()