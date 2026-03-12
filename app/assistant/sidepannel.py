"""
Chat Side Panel - AI Assistant Interface
Displays conversation with Nova AI and handles user input.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit
from PySide6.QtCore import Qt, Signal


class ChatSidePanel(QWidget):
    """
    Side panel widget for chat interface with Nova AI.
    """
    
    send_message_requested = Signal(str)
    action_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 800) 
        
        # --- NEW: State Tracking for Gaze Navigation ---
        self.action_buttons = [] # Stores a list of (button_widget, interaction_data)
        self.current_selection_index = -1 # -1 means nothing is selected yet
    
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Container with dark theme
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(18, 18, 18, 0.4); 
                border-radius: 15px;
                border: 1px solid rgba(42, 42, 42, 0.6); 
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(15)

        # Header
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("NOVA Gaze AI")
        self.title_label.setStyleSheet(
            "color: #BB86FC; font-weight: bold; font-size: 16px; border: none;"
        )
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch() 
        self.container_layout.addLayout(self.header_layout)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 30, 0.4);
                color: #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                border: none;
                font-size: 14px;
            }
        """)
        
        # Welcome message
        welcome = (
            '<span style="color: #BB86FC;"><b>Nova:</b></span> '
            'System ready. I can see your screen and help you navigate. '
            'How can I assist you?'
        )
        self.chat_display.append(welcome)
        
        self.container_layout.addWidget(self.chat_display)

        # Chat input field
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Nova... (Press Enter to send)")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 30, 0.4);
                color: white;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #00E5FF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00E5FF;
                background-color: rgba(30, 30, 30, 0.6); 
            }
        """)
        self.container_layout.addWidget(self.chat_input)

        self.layout.addWidget(self.container)
        
        # Connect input signal
        self.chat_input.returnPressed.connect(self.handle_prompt)
        
        print("[ChatSidePanel] Initialized")

    def handle_prompt(self):
        """Handle when user presses Enter in chat input."""
        user_text = self.chat_input.text().strip()
        if user_text:
            # Clear input immediately
            self.chat_input.clear()
            
            # Emit signal for parent to handle
            self.send_message_requested.emit(user_text)
            
            print(f"[ChatSidePanel] User message: {user_text}")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    panel = ChatSidePanel()
    
    # Test signal
    panel.send_message_requested.connect(
        lambda text: print(f"Signal received: {text}")
    )
    
    panel.show()
    sys.exit(app.exec())
