import os
from app.aws_nova.client import NovaAIClient

def test_api():
    print("🤖 Initializing Nova AI Client...")
    nova_client = NovaAIClient()
    
    test_image_path = "public/testing/test_image.png"