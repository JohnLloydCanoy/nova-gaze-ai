import unittest
from unittest.mock import MagicMock
from analysis import get_possible_ui_interactions

class TestVisionAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.mock_client = MagicMock()
        self.test_image_path = "test_image.png"