import sys
import os
from PySide6.QtWidgets import QApplication
from app.layout import NovaGazeOverlay
from app.aws_nova.client import NovaAIClient 

def load_stylesheet(app):
    # Load the stylesheet if it exists
    path = os.path.join("app", "assets", "styles.qss")  # FIXED typo
    # Changed 'assests' to 'assets'
    path = os.path.join("app", "assets", "styles.qss")
    if os.path.exists(path):
        with open(path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {path}")

def main():
    # Initialize Nova Client (triggers console logs)
    nova_ai = NovaAIClient() 

    app = QApplication(sys.argv)
    load_stylesheet(app)
    
    window = NovaGazeOverlay(ai_client=nova_ai) 
    window.show()
    
    print("  [✔] Nova Gaze Overlay Active.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()