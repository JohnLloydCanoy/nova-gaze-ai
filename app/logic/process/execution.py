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


def _normalize_to_screen_point(center_x: float, center_y: float) -> Optional[Tuple[int, int]]:
    screen = QApplication.primaryScreen()
    if not screen:
        return None

    geo = screen.geometry()
    # Values are normalized from 0.0 to 1.0 against the full screen.
    x = geo.x() + int(max(0.0, min(1.0, center_x)) * geo.width())
    y = geo.y() + int(max(0.0, min(1.0, center_y)) * geo.height())
    return x, y


def _windows_left_click(x: int, y: int) -> bool:
    user32 = ctypes.windll.user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    if user32.SetCursorPos(int(x), int(y)) == 0:
        return False

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

    center_x = _to_float(action_data.get("center_x"))
    center_y = _to_float(action_data.get("center_y"))

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
