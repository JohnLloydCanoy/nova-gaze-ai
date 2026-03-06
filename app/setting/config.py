import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration for Nova Gaze AI."""
    NOVA_API_KEY = os.getenv("NOVA_API_KEY")
    NOVA_BASE_URL = os.getenv("NOVA_BASE_URL")
    # Model configuration
    NOVA_VISION_MODEL = "nova-2-lite-v1"