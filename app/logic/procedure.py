import os
import logging
from typing import List, Dict
from app.aws_nova.client import NovaAIClient
from app.logic.process.take_screen_shot import capture_screen
from app.logic.process.vision_analyzer import get_possible_ui_interactions

logger = logging.getLogger(__name__)

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
        logger.info(f"[Step 2 Complete] Extracted {len(ui_interactions)} elements.")
    
    # --- FIXED EXCEPTION BLOCK ---
    except Exception as e:
        logger.error(f"Screen analysis procedure failed: {e}")
        return []
        
    finally:
        logger.info("[Step 3] Executing secure cleanup...")
        if os.path.exists(temp_screenshot_path):
            try:
                os.remove(temp_screenshot_path)
                logger.debug(f"Deleted temporary user data: {temp_screenshot_path}")
            except OSError as cleanup_error:
                logger.critical(f"Security Warning: Could not delete screenshot! {cleanup_error}")
                
        logger.info("=== Screen Analysis Procedure Finished ===")
        
    return ui_interactions