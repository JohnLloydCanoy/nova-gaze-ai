import sys
import os
from PySide6.QtWidgets import QApplication
from app.layout import NovaGazeOverlay
from app.aws_nova.client import NovaAIClient


def load_stylesheet(app):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(base_dir, "app", "assets", "styles.qss"),
        os.path.join(base_dir, "app", "assests", "styles.qss"),
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            return

    print("Warning: Stylesheet not found. Checked paths:")
    for path in candidate_paths:
        print(f"  - {path}")


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
