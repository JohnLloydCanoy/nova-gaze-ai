import os
from app.aws_nova.client import NovaAIClient

def test_api():
    print("🤖 Initializing Nova AI Client...")
    nova_client = NovaAIClient()
    
    test_image_path = "public/testing/test_image.png"
    if not os.path.exists(test_image_path):
        print(f"❌ Error: Could not find '{test_image_path}'. Please add a test screenshot to your folder.")
        return
    
    print(f"📸 Reading {test_image_path}...")
    with open(test_image_path, "rb") as image_file:
        image_bytes = image_file.read()
    print("🚀 Sending image to Amazon Nova API... (Waiting for response)")
    
    result = nova_client.analyze_gaze_target(image_bytes)
    
    if result:
        print("\n✅ SUCCESS! Connection to Amazon is working.")
        print(f"🧠 AI identified the UI element as: '{result}'")
    else:
        print("\n❌ FAILED: Did not receive a valid response. Check your API key or network.")

if __name__ == "__main__":
    test_api()