import os
import logging
import pprint
import pyautogui
from app.aws_nova.client import NovaAIClient
from app.logic.process.vision_analyzer import get_possible_ui_interactions

# Set up standard logging so we can see the internal process in the terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def run_live_test():
    """
    Captures the current screen, sends it to AWS Nova AI for interaction analysis,
    prints the structured JSON response, and securely cleans up the image file.
    """
    test_image_path = "live_test_screenshot.png"
    client = NovaAIClient()
    
    print("📸 Taking a screenshot of your current desktop...")
    
    try:
        # Capture the screen
        screenshot = pyautogui.screenshot()
        screenshot.save(test_image_path)
        logger.info(f"Screenshot temporarily saved to {test_image_path}")
        
        #  Send to Nova AI
        print("🚀 Sending image to AWS Nova AI. Please wait...")
        results = get_possible_ui_interactions(client, test_image_path)
        
        # Display the results with great DX (Pretty Print)
        print("\n" + "="*50)
        print("🎯 AI VISION ANALYSIS RESULTS")
        print("="*50)
        
        if results:
            pprint.pprint(results, indent=4)
        else:
            print("⚠️ No interactions found or an error occurred. Check the logs above.")
            
    except Exception as e:
        logger.error(f"❌ The live test failed: {e}")
        
    finally:
        # Security & Scalability: Always clean up the user's data
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            logger.info(f"🧹 Securely deleted temporary screenshot: {test_image_path}")

if __name__ == "__main__":
    run_live_test()