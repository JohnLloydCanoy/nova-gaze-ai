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
        self.mock_client.analyze_vision.return_value = fake_ai_response
        result = get_possible_ui_interactions(self.mock_client, self.test_image_path)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["element_name"], "Login Button")
        self.assertEqual(result[1]["action"], "Type")
        
    def test_markdown_stripping(self):
        """Tests that the function survives when the AI wraps JSON in markdown blocks."""
        
        fake_markdown_response = '''```json
        [
            {"element_name": "Search", "action": "Click", "description": "Search"}
        ]
        ```'''
        self.mock_client.analyze_vision.return_value = fake_markdown_response

        result = get_possible_ui_interactions(self.mock_client, self.test_image)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["element_name"], "Search")
        
    def test_bad_json_handling(self):
        """Tests that the function fails safely and consistently if the AI returns garbage."""
        
        self.mock_client.analyze_vision.return_value = "Sorry, I cannot analyze this image."
        
        result = get_possible_ui_interactions(self.mock_client, self.test_image)
        
        self.assertEqual(result, [])