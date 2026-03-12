import logging
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

def capture_screen(file_path: str) -> bool:
    """Captures the primary screen and saves it to the given file path."""
    try:
        screen = QApplication.primaryScreen()
        if not screen:
            logger.error("No primary screen detected.")
            return False
            
        screenshot = screen.grabWindow(0)
        screenshot.save(file_path, "PNG")
        return True
        
    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return False