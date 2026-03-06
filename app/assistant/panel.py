from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt

class AssistantPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setFixedHeight(200)

        # Transparent, modern background
        self.setStyleSheet("""
            background-color: rgba(30, 30, 30, 180);
            border-radius: 12px;
            padding: 2px;
            font-weight: bold;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header
        header = QLabel("Nova Assistant")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 15px;
            color: #ffffff;
            font-weight: bold;
        """)
        layout.addWidget(header)

        # Conversation Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(3)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # Example assistant message
        self.add_message("Here are some suggestions:", sender="assistant")

        # Suggested replies (vertical buttons)
        self.add_suggestions([
            "I want to eat cake!",
            "I want to eat hotdog",
            "I want to eat pizza"
        ])

    def add_message(self, text, sender="assistant"):
        bubble = QLabel(text)
        bubble.setWordWrap(True)

        if sender == "assistant":
            bubble.setStyleSheet("""
                background-color: #3a3f47;
                color: #ffffff;
                font-weight: bold;
                padding: 6px;
                border-radius: 6px;
                margin: 2px;
            """)
            bubble.setAlignment(Qt.AlignLeft)
        else:
            bubble.setStyleSheet("""
                background-color: #4a90e2;
                color: #ffffff;
                font-weight: bold;
                padding: 6px;
                border-radius: 6px;
                margin: 2px;
            """)
            bubble.setAlignment(Qt.AlignRight)

        self.messages_layout.insertWidget(self.messages_layout.count()-1, bubble)

    def add_suggestions(self, options):
        """Add clickable suggestion buttons stacked vertically."""
        for option in options:
            btn = QPushButton(option)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(220, 20, 60, 100);
                    color: #ffffff;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px;
                    margin-top: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 0, 0, 220);
                }
            """)
            # When clicked, add the option as a user message
            btn.clicked.connect(lambda _, text=option: self.add_message(text, sender="user"))
            self.messages_layout.insertWidget(self.messages_layout.count()-1, btn)