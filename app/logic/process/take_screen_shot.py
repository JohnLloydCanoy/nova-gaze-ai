import logging
import time
from typing import List

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def _hide_top_level_widgets() -> List[object]:
    hidden_widgets = []
    app = QApplication.instance()
    if not app:
        return hidden_widgets

    # Hide only currently visible top-level widgets, then restore them later.
    for widget in app.topLevelWidgets():
        if widget and widget.isVisible():
            widget.hide()
            hidden_widgets.append(widget)

    QApplication.processEvents()
    time.sleep(0.05)
    return hidden_widgets


def _restore_top_level_widgets(widgets: List[object]) -> None:
    for widget in widgets:
        widget.show()
    QApplication.processEvents()


def capture_screen_bytes() -> bytes:
    """Captures the primary screen to PNG bytes while temporarily hiding app UI."""
    hidden_widgets = []
    try:
        screen = QApplication.primaryScreen()
        if not screen:
            logger.error("No primary screen detected.")
            return b""

        hidden_widgets = _hide_top_level_widgets()
        screenshot = screen.grabWindow(0)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        screenshot.save(buffer, "PNG")
        return bytes(buffer.data())
    except Exception as e:
        logger.error(f"Failed to capture screen bytes: {e}")
        return b""
    finally:
        _restore_top_level_widgets(hidden_widgets)


def capture_screen(file_path: str) -> bool:
    """Captures the primary screen and saves it while temporarily hiding app UI."""
    hidden_widgets = []
    try:
        screen = QApplication.primaryScreen()
        if not screen:
            logger.error("No primary screen detected.")
            return False

        hidden_widgets = _hide_top_level_widgets()
        screenshot = screen.grabWindow(0)
        screenshot.save(file_path, "PNG")
        return True

    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return False
    finally:
        _restore_top_level_widgets(hidden_widgets)
