import base64
import time
from openai import OpenAI
from settings.config import Config

class NovaAIClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.NOVA_API_KEY,
            base_url=Config.NOVA_BASE_URL
        )
        self.model = Config.NOVA_VISION_MODEL
        
        # --- NEW: Conversation Memory ---
        self.chat_history = [
    {
        "role": "system", 
        "content": (
            "You are Nova Gaze AI, a specialized assistant for people with ALS. "
            "Your goal is to help users navigate their computer via eye-tracking. "
            "Be patient, proactive, and concise. When analyzing screenshots, "
            "suggest the most likely action the user wants to take."
            "Provide Suggestions what should the user do. make it in a bullet form at least 3."
        )
    }
]
        
        print(f"  [✔] Model Linked: {self.model}")
        print(f"  [✔] Chat Session Initialized.\n")

   

    def chat_with_vision(self, user_text, image_bytes=None):
        """
        Standard chatbot function that can optionally 'see' an image.
        """
        try:
            # Prepare the content block
            content = [{"type": "text", "text": user_text}]
            
            # If an image is provided, append it to the current message
            if image_bytes:
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                })

            # Add user message to history
            self.chat_history.append({"role": "user", "content": content})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                max_tokens=150 # Increased for chatbot replies
            )

            assistant_reply = response.choices[0].message.content.strip()
            
            # Save assistant reply to history for context in the next turn
            self.chat_history.append({"role": "assistant", "content": assistant_reply})
            
            return assistant_reply

        except Exception as e:
            print(f"\n  [✘] Chat Error: {e}")
            return "Sorry, I encountered an error processing that."