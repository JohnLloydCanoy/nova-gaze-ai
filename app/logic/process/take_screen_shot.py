import logging
import sys
import time
import ctypes
from typing import List, Optional

from PySide6.QtCore import QBuffer, QIODevice, QPoint
from PySide6.QtGui import QPixmap
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


def _get_foreground_window_handle() -> Optional[int]:
    if not sys.platform.startswith("win"):
        return None

    try:
        user32 = ctypes.windll.user32
        hwnd = int(user32.GetForegroundWindow())
        return hwnd or None
    except Exception:
        return None


def _capture_foreground_window_pixmap() -> Optional[QPixmap]:
    if not sys.platform.startswith("win"):
        return None

    hwnd = _get_foreground_window_handle()
    if not hwnd:
        logger.warning("Could not resolve a foreground window handle.")
        return None

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    try:
        user32 = ctypes.windll.user32
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)) == 0:
            logger.warning("GetWindowRect failed for foreground window.")
            return None

        width = max(1, int(rect.right - rect.left))
        height = max(1, int(rect.bottom - rect.top))
        center_x = int(rect.left + (width / 2))
        center_y = int(rect.top + (height / 2))

        screen = QApplication.screenAt(QPoint(center_x, center_y))
        if screen is None:
            screen = QApplication.primaryScreen()

        if not screen:
            logger.error("No screen available for foreground capture.")
            return None

        # Capture only the focused foreground window to reflect user-visible workflow.
        pixmap = screen.grabWindow(hwnd, 0, 0, width, height)
        if pixmap.isNull():
            logger.warning("Foreground window capture returned empty pixmap.")
            return None

        logger.info(
            "Captured foreground window (hwnd=%s, size=%sx%s).", hwnd, width, height)
        return pixmap

    except Exception as exc:
        logger.warning("Foreground window capture failed: %s", exc)
        return None


def _capture_desktop_pixmap() -> Optional[QPixmap]:
    screen = QApplication.primaryScreen()
    if not screen:
        logger.error("No primary screen detected.")
        return None

    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        logger.error("Desktop capture returned empty pixmap.")
        return None

    return pixmap


def _capture_best_available_pixmap() -> Optional[QPixmap]:
    foreground_pixmap = _capture_foreground_window_pixmap()
    if foreground_pixmap is not None:
        return foreground_pixmap

    logger.info("Falling back to full desktop capture.")
    return _capture_desktop_pixmap()


def capture_screen_bytes() -> bytes:
    """Captures the primary screen to PNG bytes while temporarily hiding app UI."""
    hidden_widgets = []
    try:
        hidden_widgets = _hide_top_level_widgets()
        screenshot = _capture_best_available_pixmap()
        if screenshot is None:
            return b""

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
        hidden_widgets = _hide_top_level_widgets()
        screenshot = _capture_best_available_pixmap()
        if screenshot is None:
            return False

        screenshot.save(file_path, "PNG")
        return True

    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return False
    finally:
        _restore_top_level_widgets(hidden_widgets)
