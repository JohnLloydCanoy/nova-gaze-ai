import json
import logging
from app.aws_nova.client import NovaAIClient

logger = logging.getLogger(__name__)

def get_possible_ui_interactions(nova_client: NovaAIClient, image_path: str) -> list[dict]:
    """_summary_

    Args:
        nova_client (NovaAIClient): _description_
        image_path (str): _description_

    Returns:
        list[dict]: _description_
    """
    
    system_prompt = ()
    
    logger.info(f"Requesting UI interaction analysis for {image_path}")
    
    try:
        # Submit the image and our strict prompt to the Nova client
        response_text = nova_client.analyze_vision(
            image_path=image_path,
            prompt=system_prompt
        )
        
        # Cleaning the response to ensure it's valid JSON
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        # Parse the cleaned response as JSON
        interactions = json.loads(clean_text.strip())
        
        logger.info(f"Successfully identified {len(interactions)} possible interactions.")
        return interactions
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse Nova AI response as JSON: {json_err}. Raw response: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An error occurred during interaction analysis: {e}")
        return []