from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit
from PySide6.QtCore import Qt, Signal

class ChatSidePanel(QWidget):
    send_message_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 800) 
    
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                /* #121212 converted to rgba with 40% opacity */
                background-color: rgba(18, 18, 18, 0.4); 
                border-radius: 15px;
                /* Softened the border slightly to match the glass effect */
                border: 1px solid rgba(42, 42, 42, 0.6); 
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(15)

        self.header_layout = QHBoxLayout()
        
        self.title_label = QLabel("NOVA Gaze AI")
        # Added background: transparent so it doesn't inherit the container's background stack
        self.title_label.setStyleSheet("color: #BB86FC; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch() 
        
        self.container_layout.addLayout(self.header_layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                /* #1E1E1E converted to rgba with 40% opacity */
                background-color: rgba(30, 30, 30, 0.4);
                color: #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                border: none;
                font-size: 14px;
            }
        """)
        self.chat_display.append("Nova: System ready. I can see your screen. How can I assist your navigation today?")
        self.container_layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Nova...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                /* #1E1E1E converted to rgba with 40% opacity */
                background-color: rgba(30, 30, 30, 0.4);
                color: white;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid rgba(0, 229, 255, 0.5); /* Semi-transparent cyan border */
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00E5FF;
                background-color: rgba(30, 30, 30, 0.6); /* Slightly darker when typing */
            }
        """)
        self.container_layout.addWidget(self.chat_input)

        self.layout.addWidget(self.container)
        self.chat_input.returnPressed.connect(self.handle_prompt)

    def handle_prompt(self):
        """Grabs the text, puts it in the chat, and clears the input."""
        user_text = self.chat_input.text().strip()
        if user_text:
            # Display user message
            self.chat_display.append(f'<span style="color: #00E5FF;"><b>You:</b></span> {user_text}')
            # Clear the input box
            self.chat_input.clear()
            self.send_message_requested.emit(user_text)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    panel = ChatSidePanel()
    panel.show()
    sys.exit(app.exec())