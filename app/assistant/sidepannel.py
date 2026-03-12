from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QLineEdit, QPushButton, QScrollArea, QMainWindow
)
from PySide6.QtCore import Qt, Signal

class ChatSidePanel(QWidget):
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
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

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
        self.title_label.setStyleSheet("color: #BB86FC; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch() 
        self.container_layout.addLayout(self.header_layout)

        # Chat Display
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
        self.chat_display.append("Nova: System ready. Close your eyes for 5 seconds to initiate a screen scan.")
        self.container_layout.addWidget(self.chat_display, stretch=2)

        # Dynamic Action Buttons Area
        self.buttons_scroll = QScrollArea()
        self.buttons_scroll.setWidgetResizable(True)
        self.buttons_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 10px; }
        """)
        
        self.buttons_widget = QWidget()
        self.buttons_widget.setStyleSheet("background: transparent; border: none;")
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setSpacing(10)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_scroll.setWidget(self.buttons_widget)
        
        self.container_layout.addWidget(self.buttons_scroll, stretch=1)

        # Chat Input
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask Nova...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 30, 0.4);
                color: white;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid rgba(0, 229, 255, 0.5);
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00E5FF;
                background-color: rgba(30, 30, 30, 0.6); 
            }
        """)
        self.container_layout.addWidget(self.chat_input)

        self.layout.addWidget(self.container)
        self.chat_input.returnPressed.connect(self.handle_prompt)

    def handle_prompt(self):
        user_text = self.chat_input.text().strip()
        if user_text:
            self.chat_display.append(f'<span style="color: #00E5FF;"><b>You:</b></span> {user_text}')
            self.chat_input.clear()
            self.send_message_requested.emit(user_text)
    
    def clear_action_buttons(self):
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def generate_action_buttons(self, interactions: list):
        self.clear_action_buttons() 
        self.action_buttons.clear() # Reset our tracking list
        self.current_selection_index = -1
        
        for interaction in interactions:
            element_name = interaction.get("element_name", "Unknown Element")
            action_type = interaction.get("action", "Interact")
            description = interaction.get("description", "")
            
            btn_text = f"[{action_type}] {element_name}\n({description})"
            btn = QPushButton(btn_text)
            
            # Allow manual clicking too
            btn.clicked.connect(lambda checked=False, i=interaction: self._on_action_clicked(i))
            
            self.buttons_layout.addWidget(btn)
            self.action_buttons.append((btn, interaction)) # Save it to memory
            
        # Automatically highlight the very first button
        if self.action_buttons:
            self.current_selection_index = 0
            self.update_button_styles()

    # --- NEW: Gaze Navigation Methods ---
    def select_next(self):
        """Moves selection down one button."""
        if not self.action_buttons: return
        self.current_selection_index = (self.current_selection_index + 1) % len(self.action_buttons)
        self.update_button_styles()
        # Scroll to make sure it's visible
        self.buttons_scroll.ensureWidgetVisible(self.action_buttons[self.current_selection_index][0])
        
    def select_previous(self):
        """Moves selection up one button."""
        if not self.action_buttons: return
        self.current_selection_index = (self.current_selection_index - 1) % len(self.action_buttons)
        self.update_button_styles()
        self.buttons_scroll.ensureWidgetVisible(self.action_buttons[self.current_selection_index][0])
        
    def execute_selected(self):
        """Fires the click event for the currently highlighted button."""
        if 0 <= self.current_selection_index < len(self.action_buttons):
            btn, interaction = self.action_buttons[self.current_selection_index]
            self._on_action_clicked(interaction)

    def update_button_styles(self):
        """Loops through buttons and applies a bright style to the selected one."""
        for i, (btn, _) in enumerate(self.action_buttons):
            if i == self.current_selection_index:
                # HIGHLIGHTED STYLE
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #03DAC6; 
                        color: #121212;
                        border: 2px solid #FFFFFF;
                        border-radius: 8px;
                        padding: 15px; 
                        font-size: 14px;
                        font-weight: bold;
                        text-align: left;
                    }
                """)
            else:
                # NORMAL STYLE
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(3, 218, 198, 0.2); 
                        color: #03DAC6;
                        border: 1px solid #03DAC6;
                        border-radius: 8px;
                        padding: 15px; 
                        font-size: 13px;
                        font-weight: bold;
                        text-align: left;
                    }
                """)

    def _on_action_clicked(self, interaction_data: dict):
        self.chat_display.append(f'<span style="color: #03DAC6;"><b>System:</b> Executing {interaction_data.get("action")} on {interaction_data.get("element_name")}...</span>')
        self.action_selected.emit(interaction_data)