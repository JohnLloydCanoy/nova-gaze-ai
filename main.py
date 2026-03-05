import sys
from PySide6.QtWidgets import QApplication
from app.layout import NovaGazeOverlay

def load_stylesheet(app):
    # Load the stylesheet if it exists
    path = os.path.join("app", "assests", "styles.qss")
    if os.path.exists(path):
        with open(path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {path}")

def main():
    app = QApplication(sys.argv)
    
    load_stylesheet(app)
    
    window = NovaGazeOverlay()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()