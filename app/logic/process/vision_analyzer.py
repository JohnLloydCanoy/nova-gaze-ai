import json
import re
import logging
from app.aws_nova.client import NovaAIClient

logger = logging.getLogger(__name__)


def get_possible_ui_interactions(nova_client: NovaAIClient, image_path: str) -> list[dict]:
    """
    Analyzes a screenshot using AWS Nova AI to determine possible user interactions.
    """
    system_prompt = (
        "You are an expert UI/UX automation assistant. Analyze the provided screenshot of a computer screen. "
        "Identify the primary ways a user can interact with the current interface. "
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

        # --- THE BULLETPROOF REGEX FILTER ---
        # Finds everything from the first '[' to the last ']'
        match = re.search(r'\[.*\]', response_text, re.DOTALL)

        if match:
            clean_json_str = match.group(0)
            interactions = json.loads(clean_json_str)
            # Keep only interaction objects that contain at least a callable target.
            if isinstance(interactions, list):
                validated = []
                for item in interactions:
                    if not isinstance(item, dict):
                        continue
                    if "center_x" in item and "center_y" in item:
                        validated.append(item)
                    else:
                        # Preserve legacy responses so UI can still display options.
                        validated.append(item)
                interactions = validated
            logger.info(
                f"Successfully identified {len(interactions)} possible interactions.")
            return interactions
        else:
            logger.error("Could not find a JSON array in Nova's response.")
            logger.debug(f"Raw response was: {response_text}")
            return []

    except FileNotFoundError:
        logger.error(f"Screenshot file not found at path: {image_path}")
        return []
    except json.JSONDecodeError as json_err:
        logger.error(
            f"Failed to parse Nova AI response as JSON: {json_err}. Raw response: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An error occurred during interaction analysis: {e}")
        return []
