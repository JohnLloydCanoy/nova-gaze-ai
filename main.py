import sys
import os
from PySide6.QtWidgets import QApplication
from app.layout import NovaGazeOverlay
from app.aws_nova.client import NovaAIClient

def load_stylesheet(app):
    path = os.path.join("app", "assests", "styles.qss")
    if os.path.exists(path):
        with open(path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {path}")

def main():
    # 1. Initialize the Chat Bot Client first
    print("🚀 Initializing Nova Gaze AI...")
    nova_ai = NovaAIClient() 

    # 2. Setup the GUI
    app = QApplication(sys.argv)
    load_stylesheet(app)
    
    # 3. Pass the 'nova_ai' instance into the overlay
    window = NovaGazeOverlay(ai_client=nova_ai) 
    
    window.show()
    print("✅ System Ready - Blink to activate")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()