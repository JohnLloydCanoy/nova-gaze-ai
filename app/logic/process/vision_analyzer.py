import json
import re
import logging
from app.aws_nova.client import NovaAIClient

logger = logging.getLogger(__name__)


def _extract_json_payload(response_text: str):
    """Extract the first decodable JSON payload (list or object) from model text."""
    if not response_text:
        return None

    text = response_text.strip()
    decoder = json.JSONDecoder()

    # Fast path: whole response is valid JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code fences first if present.
    fence_matches = re.findall(
        r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    for chunk in fence_matches:
        chunk = chunk.strip()
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            continue

    # Fallback: scan text for first decodable JSON object/array.
    for index, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
            return payload
        except json.JSONDecodeError:
            continue

    return None


def _normalize_interaction_payload(payload) -> list[dict]:
    """Normalize model payload into list[dict] interactions."""
    interactions = []

    if isinstance(payload, list):
        interactions = payload
    elif isinstance(payload, dict):
        list_keys = (
            "interactions",
            "ui_interactions",
            "possible_interactions",
            "actions",
            "elements",
            "targets",
        )
        for key in list_keys:
            value = payload.get(key)
            if isinstance(value, list):
                interactions = value
                break

        if not interactions and all(k in payload for k in ("element_name", "action")):
            interactions = [payload]

    if not isinstance(interactions, list):
        return []

    validated: list[dict] = []
    for item in interactions:
        if isinstance(item, dict):
            validated.append(item)

    return validated


def get_possible_ui_interactions(nova_client: NovaAIClient, image_path: str) -> list[dict]:
    """
    Analyzes a screenshot using AWS Nova AI to determine possible user interactions.
    """
    system_prompt = (
        "You are an expert UI/UX automation assistant. Analyze the provided screenshot of a computer screen. "
        "Identify the primary ways a user can interact with the current interface. "
        "Prioritize controls that belong to the active application content area. "
        "Do not return operating-system shell controls such as Start menu/button, Taskbar, desktop background, system tray, or clock. "
        "Return the result STRICTLY as a JSON array of objects. Do not include any markdown formatting, "
        "code blocks, or conversational text. "
        "Each object must have the following keys: "
        "'element_name' (e.g., 'Submit Button', 'Search Bar'), "
        "'action' (e.g., 'Click', 'Type'), and "
        "'description' (e.g., 'Submits the login form'), "
        "'center_x' (normalized number between 0.0 and 1.0), and "
        "'center_y' (normalized number between 0.0 and 1.0). "
        "The coordinates must point to the center of the target UI element."
    )

    logger.info(f"Requesting UI interaction analysis for {image_path}")

    try:
        # 1. Safely read the image
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        # 2. Submit to AWS Nova
        response_text = nova_client.chat_with_vision(
            user_text=system_prompt,
            image_bytes=image_bytes
        )

        payload = _extract_json_payload(response_text)
        interactions = _normalize_interaction_payload(payload)

        if interactions:
            logger.info(
                f"Successfully identified {len(interactions)} possible interactions.")
            return interactions

        logger.error(
            "Could not extract valid interaction objects from Nova response.")
        logger.warning("Response preview: %s", (response_text or "")[:500])
        return []

    except FileNotFoundError:
        logger.error(f"Screenshot file not found at path: {image_path}")
        return []
    except Exception as e:
        logger.error(f"An error occurred during interaction analysis: {e}")
        return []
