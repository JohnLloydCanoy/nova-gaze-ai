import os
from app.aws_nova.client import NovaAIClient

def test_api():
    print("🤖 Initializing Nova AI Client...")
    nova_client = NovaAIClient()
    
    test_image_path = "public/testing/test_image.png"
    if not os.path.exists(test_image_path):
        print(f"❌ Error: Could not find '{test_image_path}'. Please add a test screenshot to your folder.")
        return
    
    