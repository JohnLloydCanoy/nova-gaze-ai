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