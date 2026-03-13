import os
import logging
from typing import List, Dict
from app.aws_nova.client import NovaAIClient
from app.logic.process.take_screen_shot import capture_screen, get_last_capture_context
from app.logic.process.vision_analyzer import get_possible_ui_interactions

logger = logging.getLogger(__name__)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_capture_context_to_interactions(ui_interactions: List[Dict]) -> List[Dict]:
    """Convert screenshot-relative coordinates into virtual desktop normalized coordinates."""
    if not ui_interactions:
        return ui_interactions

    context = get_last_capture_context()
    origin_x = _to_float(context.get("origin_x"))
    origin_y = _to_float(context.get("origin_y"))
    capture_width = _to_float(context.get("width"))
    capture_height = _to_float(context.get("height"))
    virtual_x = _to_float(context.get("virtual_x"))
    virtual_y = _to_float(context.get("virtual_y"))
    virtual_width = _to_float(context.get("virtual_width"))
    virtual_height = _to_float(context.get("virtual_height"))

    required = [origin_x, origin_y, capture_width,
                capture_height, virtual_x, virtual_y, virtual_width, virtual_height]
    if any(v is None for v in required):
        return ui_interactions

    if capture_width <= 0 or capture_height <= 0 or virtual_width <= 0 or virtual_height <= 0:
        return ui_interactions

    remapped = []
    for item in ui_interactions:
        if not isinstance(item, dict):
            continue

        cx = _to_float(item.get("center_x"))
        cy = _to_float(item.get("center_y"))

        if cx is None or cy is None:
            remapped.append(item)
            continue

        abs_x = origin_x + (_clamp01(cx) * capture_width)
        abs_y = origin_y + (_clamp01(cy) * capture_height)

        item = dict(item)
        item["absolute_x"] = int(round(abs_x))
        item["absolute_y"] = int(round(abs_y))
        item["center_x"] = _clamp01((abs_x - virtual_x) / virtual_width)
        item["center_y"] = _clamp01((abs_y - virtual_y) / virtual_height)
        remapped.append(item)

    return remapped


def _print_terminal_choices(ui_interactions: List[Dict]) -> None:
    # Terminal tracker for quick visibility of scan choices.
    print("\n=== DETECTED UI CHOICES ===")
    if not ui_interactions:
        print("0. No clickable UI choices found")
        print("===========================\n")
        return

    for index, interaction in enumerate(ui_interactions, start=1):
        element_name = str(interaction.get(
            "element_name", "Unknown Element")).strip()
        action_name = str(interaction.get("action", "Interact")).strip()
        if not element_name:
            element_name = "Unknown Element"
        if not action_name:
            action_name = "Interact"
        print(f"{index}. {element_name} [{action_name}]")

    print("===========================\n")


def execute_screen_analysis_procedure(nova_client: NovaAIClient) -> List[Dict]:
    """
    Master procedure that securely orchestrates capturing the user's screen,
    analyzing it for UI interactions, and cleaning up the sensitive image data.
    """

    temp_screenshot_path = "secure_temp_capture.png"
    ui_interactions = []

    logger.info("=== Starting Screen Analysis Procedure ===")

    try:
        logger.info("[Step 1] Triggering screen capture...")

        capture_success = capture_screen(file_path=temp_screenshot_path)

        if not capture_success or not os.path.exists(temp_screenshot_path):
            logger.error("Procedure aborted: Failed to capture the screen.")
            return []

        logger.info("[Step 2] Sending capture to AWS Nova AI for analysis...")

        ui_interactions = get_possible_ui_interactions(
            nova_client=nova_client,
            image_path=temp_screenshot_path
        )
        ui_interactions = _apply_capture_context_to_interactions(
            ui_interactions)
        _print_terminal_choices(ui_interactions)
        logger.info(
            f"[Step 2 Complete] Extracted {len(ui_interactions)} elements.")

    # --- FIXED EXCEPTION BLOCK ---
    except Exception as e:
        logger.error(f"Screen analysis procedure failed: {e}")
        return []

    finally:
        logger.info("[Step 3] Executing secure cleanup...")
        if os.path.exists(temp_screenshot_path):
            try:
                os.remove(temp_screenshot_path)
                logger.debug(
                    f"Deleted temporary user data: {temp_screenshot_path}")
            except OSError as cleanup_error:
                logger.critical(
                    f"Security Warning: Could not delete screenshot! {cleanup_error}")

        logger.info("=== Screen Analysis Procedure Finished ===")

    return ui_interactions
