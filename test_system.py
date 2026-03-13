import logging
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtWidgets import QApplication

from app.aws_nova.client import NovaAIClient
from app.logic.procedure import execute_screen_analysis_procedure
from app.logic.process.execution import execute_interaction_action


logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


MIN_REQUIRED_CLICKS = 3
MAX_SCAN_ROUNDS = 10
POST_CLICK_DELAY_SECONDS = 1.8


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_coordinates(interaction: Dict) -> bool:
    return _to_float(interaction.get("center_x")) is not None and _to_float(interaction.get("center_y")) is not None


def _is_click_like_action(action: str) -> bool:
    action_norm = _normalize_text(action)
    click_tokens = ("click", "select", "open", "press", "tap", "type")
    return any(token in action_norm for token in click_tokens)


def _interaction_signature(interaction: Dict) -> Tuple[str, float, float]:
    element_name = _normalize_text(str(interaction.get("element_name", "")))
    center_x = _to_float(interaction.get("center_x"))
    center_y = _to_float(interaction.get("center_y"))

    # Rounded normalized coordinates help identify the same UI element across scans.
    x = round(center_x, 3) if center_x is not None else -1.0
    y = round(center_y, 3) if center_y is not None else -1.0
    return element_name, x, y


def _score_interaction(interaction: Dict) -> int:
    element_name = _normalize_text(str(interaction.get("element_name", "")))
    description = _normalize_text(str(interaction.get("description", "")))
    action_name = _normalize_text(str(interaction.get("action", "")))

    haystack = f"{element_name} {description} {action_name}"
    score = 0

    if _has_coordinates(interaction):
        score += 5

    if _is_click_like_action(action_name):
        score += 3

    if element_name and "unknown" not in element_name:
        score += 1

    # De-prioritize likely non-actionable or decorative elements.
    weak_tokens = ("logo", "background", "image", "decoration")
    if any(token in haystack for token in weak_tokens):
        score -= 2

    # De-prioritize potentially unavailable actions.
    if "disabled" in haystack or "not clickable" in haystack:
        score -= 4

    return score


def _pick_best_interaction(interactions: List[Dict], used_signatures: Set[Tuple[str, float, float]]) -> Optional[Dict]:
    if not interactions:
        return None

    candidates = []
    for interaction in interactions:
        if not _has_coordinates(interaction):
            continue
        sig = _interaction_signature(interaction)
        if sig in used_signatures:
            continue
        candidates.append(interaction)

    if not candidates:
        return None

    ranked = sorted(candidates, key=_score_interaction, reverse=True)

    if _score_interaction(ranked[0]) <= 0:
        return None

    return ranked[0]


def run_screen_interaction_simulation() -> bool:
    print("\n=== SCREEN-DRIVEN ACTION EXECUTION TEST ===")
    print("Keep the target app/window visible on screen.")
    print(
        f"This test will detect current visible UI and click at least {MIN_REQUIRED_CLICKS} interactive elements."
    )
    print("The mouse will move/click automatically.\n")

    for seconds in range(5, 0, -1):
        print(f"Starting in {seconds}...")
        time.sleep(1)

    nova_client = NovaAIClient()
    used_signatures: Set[Tuple[str, float, float]] = set()
    clicked_elements: List[str] = []
    failed_attempts = 0

    for round_number in range(1, MAX_SCAN_ROUNDS + 1):
        if len(clicked_elements) >= MIN_REQUIRED_CLICKS:
            break

        print(
            f"\n[SCAN {round_number}/{MAX_SCAN_ROUNDS}] "
            f"Clicks completed: {len(clicked_elements)}/{MIN_REQUIRED_CLICKS}"
        )
        interactions = execute_screen_analysis_procedure(nova_client)

        if not interactions:
            failed_attempts += 1
            print("[WARN] No interactions detected in this scan. Retrying...")
            time.sleep(1.0)
            continue

        selected = _pick_best_interaction(interactions, used_signatures)
        if not selected:
            failed_attempts += 1
            print(
                "[WARN] No new executable interactive element found in this scan."
            )
            time.sleep(1.0)
            continue

        selected_name = selected.get("element_name", "Unknown Element")
        selected_action = selected.get("action", "Click")
        signature = _interaction_signature(selected)
        used_signatures.add(signature)

        print(f"[SELECTED] {selected_name} [{selected_action}]")
        success, message = execute_interaction_action(selected)
        print(f"[ACTION] {message}")

        if not success:
            failed_attempts += 1
            time.sleep(1.0)
            continue

        clicked_elements.append(str(selected_name))
        time.sleep(POST_CLICK_DELAY_SECONDS)

    if len(clicked_elements) < MIN_REQUIRED_CLICKS:
        print(
            "\n[FAIL] Could not complete the minimum interactive clicks "
            f"({len(clicked_elements)}/{MIN_REQUIRED_CLICKS})."
        )
        print("Successful targets:")
        for index, name in enumerate(clicked_elements, start=1):
            print(f"{index}. {name}")
        print(f"Total retry/failed scans: {failed_attempts}")
        return False

    print(
        "\n[SUCCESS] Simulation finished: "
        f"{len(clicked_elements)} interactive UI clicks executed."
    )
    return True


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    ok = run_screen_interaction_simulation()
    sys.exit(0 if ok else 1)
