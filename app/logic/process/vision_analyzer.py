import json
import logging
from app.aws_nova.client import NovaAIClient

logger = logging.getLogger(__name__)

def get_possible_ui_interactions(nova_client: NovaAIClient, image_path: str) -> list[dict]:
    """
    Analyzes a screenshot using AWS Nova AI to determine possible user interactions.
    
    Args:
        nova_client: An initialized instance of the NovaAIClient.
        image_path: The file path to the screenshot to be analyzed.
        
    Returns:
        A list of dictionaries containing the interactive elements and their actions.
        Returns an empty list if analysis fails or parsing errors occur.
    """
    # Define a strict system prompt to guide Nova AI's analysis towards identifying actionable UI elements.
    system_prompt = (
        "You are an expert UI/UX automation assistant. Analyze the provided screenshot of a computer screen."
        "Identify the primary ways a user can interact with the current interface."
        "Return the result STRICTLY as a JSON array of objects. Do not include any markdown formatting,"
        "code blocks, or conversational text."
        "Each object must have the following keys:"
        "'element_name' (e.g., 'Submit Button', 'Search Bar'),"
        "'action' (e.g., 'Click', 'Type'), and"
        "'description' (e.g., 'Submits the login form')."
    )
    
    logger.info(f"Requesting UI interaction analysis for {image_path}")
    
    try:
        # 1. Safely read the image file into bytes for the client
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        # 2. Submit the image bytes and our strict prompt to your actual client method
        response_text = nova_client.chat_with_vision(
            user_text=system_prompt,
            image_bytes=image_bytes
        )
        
        # Cleaning the response to ensure it's valid JSON
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        interactions = json.loads(clean_text.strip())
        
        logger.info(f"Successfully identified {len(interactions)} possible interactions.")
        return interactions
        
    except FileNotFoundError:
        logger.error(f"Screenshot file not found at path: {image_path}")
        return []
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse Nova AI response as JSON: {json_err}. Raw response: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An error occurred during interaction analysis: {e}")
        return []