import unittest
from unittest.mock import MagicMock
from analysis import get_possible_ui_interactions

class TestVisionAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.mock_client = MagicMock()
        self.test_image_path = "test_image.png"
        
    def test_success_interaction_parsing(self):
        """Tests that the function correctly parses a perfect JSON response."""
        fake_ai_response = """
        [
            {"element_name": "Login Button", "action": "Click", "description": "Logs the user in"},
            {"element_name": "Username Field", "action": "Type", "description": "Enter username here"}
        ]
        """