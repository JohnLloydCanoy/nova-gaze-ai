import logging
import sys
import time
import ctypes
from ctypes import wintypes
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QBuffer, QIODevice, QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


_DPI_AWARENESS_INITIALIZED = False


_LAST_CAPTURE_CONTEXT: Dict[str, int | str] = {
    "mode": "none",
    "origin_x": 0,
    "origin_y": 0,
    "width": 0,
    "height": 0,
    "virtual_x": 0,
    "virtual_y": 0,
    "virtual_width": 1,
    "virtual_height": 1,
}


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


def _set_last_capture_context(context: Dict[str, int | str]) -> None:
    _LAST_CAPTURE_CONTEXT.clear()
    _LAST_CAPTURE_CONTEXT.update(context)


def get_last_capture_context() -> Dict[str, int | str]:
    return dict(_LAST_CAPTURE_CONTEXT)


def _ensure_windows_dpi_awareness() -> None:
    global _DPI_AWARENESS_INITIALIZED
    if _DPI_AWARENESS_INITIALIZED or not sys.platform.startswith("win"):
        return

    user32 = ctypes.windll.user32
    awareness_set = False

    # Try per-monitor v2 awareness first (best accuracy on mixed-DPI setups).
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        dpi_context = ctypes.c_void_p(-4)
        awareness_set = bool(user32.SetProcessDpiAwarenessContext(dpi_context))
    except Exception:
        awareness_set = False

    if not awareness_set:
        try:
            awareness_set = bool(user32.SetProcessDPIAware())
        except Exception:
            awareness_set = False

    if awareness_set:
        logger.info(
            "Enabled Windows DPI awareness for accurate capture/click mapping.")
    else:
        logger.warning(
            "Could not set Windows DPI awareness. Click accuracy may be reduced on scaled displays.")

    _DPI_AWARENESS_INITIALIZED = True


def _get_window_bounds(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    # Prefer DWM extended frame bounds to avoid drop-shadow offsets.
    try:
        rect = RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        dwmapi = ctypes.windll.dwmapi
        hr = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if int(hr) == 0:
            left, top, right, bottom = int(rect.left), int(
                rect.top), int(rect.right), int(rect.bottom)
            if right > left and bottom > top:
                return left, top, right, bottom
    except Exception:
        pass

    try:
        rect = RECT()
        user32 = ctypes.windll.user32
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)) != 0:
            left, top, right, bottom = int(rect.left), int(
                rect.top), int(rect.right), int(rect.bottom)
            if right > left and bottom > top:
                return left, top, right, bottom
    except Exception:
        pass

    return None


def _get_virtual_desktop_geometry() -> Tuple[int, int, int, int]:
    if sys.platform.startswith("win"):
        _ensure_windows_dpi_awareness()
        user32 = ctypes.windll.user32
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79

        x = int(user32.GetSystemMetrics(SM_XVIRTUALSCREEN))
        y = int(user32.GetSystemMetrics(SM_YVIRTUALSCREEN))
        width = max(1, int(user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)))
        height = max(1, int(user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)))
        return x, y, width, height

    screens = QApplication.screens()
    if not screens:
        return 0, 0, 1, 1

    min_x = min(screen.geometry().x() for screen in screens)
    min_y = min(screen.geometry().y() for screen in screens)
    max_right = max(screen.geometry().x() + screen.geometry().width()
                    for screen in screens)
    max_bottom = max(screen.geometry().y() + screen.geometry().height()
                     for screen in screens)

    width = max(1, int(max_right - min_x))
    height = max(1, int(max_bottom - min_y))
    return int(min_x), int(min_y), width, height


def _get_foreground_window_handle() -> Optional[int]:
    if not sys.platform.startswith("win"):
        return None

    try:
        user32 = ctypes.windll.user32
        hwnd = int(user32.GetForegroundWindow())
        return hwnd or None
    except Exception:
        return None


def _capture_foreground_window_pixmap() -> Optional[Tuple[QPixmap, Dict[str, int | str]]]:
    if not sys.platform.startswith("win"):
        return None

    _ensure_windows_dpi_awareness()

    hwnd = _get_foreground_window_handle()
    if not hwnd:
        logger.warning("Could not resolve a foreground window handle.")
        return None

    try:
        bounds = _get_window_bounds(hwnd)
        if bounds is None:
            logger.warning(
                "Failed to resolve stable frame bounds for foreground window.")
            return None

        left, top, right, bottom = bounds

        width = max(1, int(right - left))
        height = max(1, int(bottom - top))
        center_x = int(left + (width / 2))
        center_y = int(top + (height / 2))

        screen = QApplication.screenAt(QPoint(center_x, center_y))
        if screen is None:
            screen = QApplication.primaryScreen()

        if not screen:
            logger.error("No screen available for foreground capture.")
            return None

        virtual_x, virtual_y, virtual_width, virtual_height = _get_virtual_desktop_geometry()

        # Capture only the focused foreground window to reflect user-visible workflow.
        pixmap = screen.grabWindow(hwnd, 0, 0, width, height)
        if pixmap.isNull():
            logger.warning("Foreground window capture returned empty pixmap.")
            return None

        logger.info(
            "Captured foreground window (hwnd=%s, size=%sx%s).", hwnd, width, height)
        context = {
            "mode": "foreground-window",
            "origin_x": int(left),
            "origin_y": int(top),
            "width": width,
            "height": height,
            "virtual_x": virtual_x,
            "virtual_y": virtual_y,
            "virtual_width": virtual_width,
            "virtual_height": virtual_height,
        }
        return pixmap, context

    except Exception as exc:
        logger.warning("Foreground window capture failed: %s", exc)
        return None


def _capture_desktop_pixmap() -> Optional[Tuple[QPixmap, Dict[str, int | str]]]:
    virtual_x, virtual_y, virtual_width, virtual_height = _get_virtual_desktop_geometry()
    screen = QApplication.primaryScreen()
    if not screen:
        logger.error("No primary screen detected.")
        return None

    pixmap = screen.grabWindow(
        0, virtual_x, virtual_y, virtual_width, virtual_height)
    if pixmap.isNull():
        logger.error("Desktop capture returned empty pixmap.")
        return None

    context = {
        "mode": "virtual-desktop",
        "origin_x": virtual_x,
        "origin_y": virtual_y,
        "width": virtual_width,
        "height": virtual_height,
        "virtual_x": virtual_x,
        "virtual_y": virtual_y,
        "virtual_width": virtual_width,
        "virtual_height": virtual_height,
    }
    return pixmap, context


def _capture_best_available_pixmap() -> Optional[Tuple[QPixmap, Dict[str, int | str]]]:
    foreground_capture = _capture_foreground_window_pixmap()
    if foreground_capture is not None:
        return foreground_capture

    logger.info("Falling back to full desktop capture.")
    return _capture_desktop_pixmap()


def capture_screen_bytes() -> bytes:
    """Captures the primary screen to PNG bytes while temporarily hiding app UI."""
    hidden_widgets = []
    try:
        hidden_widgets = _hide_top_level_widgets()
        capture_result = _capture_best_available_pixmap()
        if capture_result is None:
            return b""

        screenshot, context = capture_result
        _set_last_capture_context(context)

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
        capture_result = _capture_best_available_pixmap()
        if capture_result is None:
            return False

        screenshot, context = capture_result
        _set_last_capture_context(context)

        screenshot.save(file_path, "PNG")
        return True

    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        return False
    finally:
        _restore_top_level_widgets(hidden_widgets)
