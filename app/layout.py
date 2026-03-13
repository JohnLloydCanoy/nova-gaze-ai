import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from app.components.tab import TopControlTab
from app.vision.camera import CameraFeedWidget
from app.assistant.sidepannel import ChatSidePanel
from app.logic.procedure import execute_screen_analysis_procedure
from app.logic.process.execution import execute_interaction_action
from app.logic.process.take_screen_shot import capture_screen_bytes


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

        # Wire the camera's gaze events to our master overlay
        self.camera_widget.thread.gaze_action_signal.connect(
            self.handle_gaze_action)

        self.top_tab = TopControlTab(self)
        self.top_tab.close_requested.connect(QApplication.instance().quit)

        center_x = (screen_geo.width() // 2) - (self.top_tab.width() // 2)
        self.top_tab.move(center_x, 20)

        self.side_panel = ChatSidePanel(self)

        panel_x = screen_geo.width() - self.side_panel.width() - 20
        panel_y = (screen_geo.height() - self.side_panel.height()) // 2
        self.side_panel.move(panel_x, panel_y)

        self.side_panel.send_message_requested.connect(self.handle_ai_chat)
        self.side_panel.action_selected.connect(self.handle_button_click)

    def closeEvent(self, event):
        """Safely shuts down the camera thread before the app closes."""
        if hasattr(self, 'camera_widget'):
            self.camera_widget.shutdown()
        event.accept()

    # --- FUNCTION 1: Handles Eye Movements from the Camera ---
    def handle_gaze_action(self, action: str):
        """Translates eye movements into application commands."""

        if action == "SCAN":
            self.side_panel.chat_display.append(
                '<span style="color: #00E5FF;"><b>System:</b> 5-Second eye closure detected. Initiating Scan...</span>')
            self.handle_ai_chat("scan")
            return

        # --- THE GATEKEEPER ---
        # Ignore eye movements if there are no buttons on the screen
        if self.side_panel.buttons_layout.count() == 0:
            return

        # Execute navigation methods if buttons exist
        if action == "SELECT_UP":
            self.side_panel.chat_display.append(
                '<span style="color: #03DAC6;"><b>System:</b> Moving selection UP...</span>')
            self.side_panel.select_previous()

        elif action == "SELECT_DOWN":
            self.side_panel.chat_display.append(
                '<span style="color: #03DAC6;"><b>System:</b> Moving selection DOWN...</span>')
            self.side_panel.select_next()

        elif action == "CLICK":
            self.side_panel.chat_display.append(
                '<span style="color: #FF5252;"><b>System:</b> Executing CLICK on selection!</span>')
            self.side_panel.execute_selected()

    # --- FUNCTION 2: Handles Text Input and the Actual AI Scan ---
    def handle_ai_chat(self, text):
        """Handles text commands or triggered scans."""
        text_lower = text.lower()

        if "scan" in text_lower or "look" in text_lower:
            self.side_panel.chat_display.append(
                '<span style="color: #BB86FC;"><b>Nova:</b> Scanning your screen...</span>')
            real_ai_data = execute_screen_analysis_procedure(self.nova)

            # --- THE MISSING CODE: This draws the buttons! ---
            if real_ai_data:
                self.side_panel.chat_display.append(
                    f'<span style="color: #03DAC6;"><b>Nova:</b> Found {len(real_ai_data)} actions.</span>')
                self.side_panel.generate_action_buttons(real_ai_data)
            else:
                self.side_panel.chat_display.append(
                    '<span style="color: #FF5252;"><b>Nova:</b> No clear interactions found.</span>')
        else:
            image_bytes = self.capture_screen()

            reply = self.nova.chat_with_vision(text, image_bytes)
            formatted_reply = f'<br><span style="color: #BB86FC;"><b>Nova:</b></span> {reply}<br>'
            self.side_panel.chat_display.append(formatted_reply)

            if hasattr(self.top_tab, 'add_assistant_message'):
                self.top_tab.add_assistant_message(reply)

    # --- FUNCTION 3: Handles the Final Button Click Execution ---
    def handle_button_click(self, action_data: dict):
        action = action_data.get('action', 'Unknown Action')
        element = action_data.get('element_name', 'Unknown Element')
        self.side_panel.chat_display.append(
            f'<span style="color: #03DAC6;"><b>System:</b> Preparing to execute {action} on {element}.</span>')

        # Hide overlay briefly so it does not block the target click.
        self.hide()
        QApplication.processEvents()
        try:
            success, message = execute_interaction_action(action_data)
        finally:
            self.show()
            QApplication.processEvents()

        color = "#03DAC6" if success else "#FF5252"
        self.side_panel.chat_display.append(
            f'<span style="color: {color};"><b>System:</b> {message}</span>')

    def capture_screen(self):
        return capture_screen_bytes()
