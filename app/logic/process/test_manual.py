import logging
import os
from app.aws_nova.client import NovaAIClient
from vision_analyzer import get_possible_ui_interactions

logging.basicConfig(level=logging.INFO)

def run_manual_test():
    test_image_path = "sample_screen.png" ## Replace with your actual test image path