import ctypes
import logging
import sys
import time
from typing import Optional, Tuple

from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> Optional[int]:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _normalize_to_screen_point(center_x: float, center_y: float) -> Optional[Tuple[int, int]]:
    screens = QApplication.screens()
    if not screens:
        return None

    min_x = min(screen.geometry().x() for screen in screens)
    min_y = min(screen.geometry().y() for screen in screens)
    max_right = max(screen.geometry().x() + screen.geometry().width()
                    for screen in screens)
    max_bottom = max(screen.geometry().y() + screen.geometry().height()
                     for screen in screens)

    width = max(1, int(max_right - min_x))
    height = max(1, int(max_bottom - min_y))

    # Values are normalized from 0.0 to 1.0 against the virtual desktop bounds.
    x = min_x + int(max(0.0, min(1.0, center_x)) * width)
    y = min_y + int(max(0.0, min(1.0, center_y)) * height)
    return x, y


def _windows_left_click(x: int, y: int) -> bool:
    user32 = ctypes.windll.user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def _cursor_is_at_target(tx: int, ty: int, tolerance: int = 2) -> bool:
        point = POINT()
        if user32.GetCursorPos(ctypes.byref(point)) == 0:
            return False
        return abs(int(point.x) - tx) <= tolerance and abs(int(point.y) - ty) <= tolerance

    if user32.SetCursorPos(int(x), int(y)) == 0:
        return False

    # Let the cursor settle and retry once if Windows has not reached target yet.
    time.sleep(0.02)
    if not _cursor_is_at_target(int(x), int(y)):
        if user32.SetCursorPos(int(x), int(y)) == 0:
            return False
        time.sleep(0.03)

    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    return True


def execute_interaction_action(action_data: dict) -> tuple[bool, str]:
    """
    Execute a selected UI action by clicking its predicted target location.
    Expected fields: element_name, action, center_x, center_y.
    """
    element = action_data.get("element_name", "Unknown Element")
    action = str(action_data.get("action", "Click"))

    absolute_x = _to_int(action_data.get("absolute_x"))
    absolute_y = _to_int(action_data.get("absolute_y"))

    center_x = _to_float(action_data.get("center_x"))
    center_y = _to_float(action_data.get("center_y"))

    if absolute_x is None or absolute_y is None:
        if center_x is None or center_y is None:
            msg = f"Missing coordinates for {element}. Run scan again to refresh targets."
            logger.warning(msg)
            return False, msg

        point = _normalize_to_screen_point(center_x, center_y)
        if not point:
            msg = "No primary screen available for execution."
            logger.error(msg)
            return False, msg
        x, y = point
    else:
        x, y = absolute_x, absolute_y

    if x is None or y is None:
        msg = f"Missing coordinates for {element}. Run scan again to refresh targets."
        logger.warning(msg)
        return False, msg

    action_lower = action.lower()

    # Most UI intents in this app map to a single left click at target center.
    supported_tokens = ("click", "select", "open", "press", "tap", "type")
    if not any(token in action_lower for token in supported_tokens):
        logger.info("Unsupported action '%s'. Falling back to click.", action)

    if sys.platform.startswith("win"):
        ok = _windows_left_click(x, y)
    else:
        msg = f"Platform '{sys.platform}' is not currently supported for native click execution."
        logger.error(msg)
        return False, msg

    if not ok:
        msg = f"Failed to click target for {element}."
        logger.error(msg)
        return False, msg

    msg = f"Executed {action} on {element} at ({x}, {y})."
    logger.info(msg)
    return True, msg
