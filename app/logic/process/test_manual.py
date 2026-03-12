import logging
import os
from app.aws_nova.client import NovaAIClient
from vision_analyzer import get_possible_ui_interactions

logging.basicConfig(level=logging.INFO)

def run_manual_test():
    test_image_path = "sample_screen.png" ## Replace with your actual test image path
    
    if not os.path.exists(test_image_path):
        with open(test_image_path, "wb") as f:
            f.write(b"dummy image data")  # Create an empty file for testing purposes
    nova_client = NovaAIClient()  
    print("Sending request to Nova AI...")
    results = get_possible_ui_interactions(client, test_image_path)