import base64
from openai import OpenAI
from settings.config import Config

class NovaAIClient:
    def __init__(self):
        # We use the standard OpenAI client pointed at Amazon's Developer URL
        self.client = OpenAI(
            api_key=Config.NOVA_API_KEY,
            base_url=Config.NOVA_BASE_URL
        )
        self.model = Config.NOVA_VISION_MODEL

    def analyze_gaze_target(self, image_bytes):
        """
        Converts a screenshot to Base64 and asks Amazon Nova to identify the UI element.
        """
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Analyze this cropped screenshot of a computer UI. What specific button, link, or element is in the center? Reply with a maximum of 3 words, like 'Reply Button' or 'Search Bar'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10 
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error communicating with Amazon Nova: {e}")
            return None