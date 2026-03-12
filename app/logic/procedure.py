# This is were we sort out the procedure for the app, such as how to handle the data, how to train the model, and how to make predictions.

import os 
import logging
from typing import List, Dict
from app.aws_nova.client import NovaAIClient
from app.logic.process.take_screen_shot import capture_screen 
from app.logic.process.vision_analyzer import get_possible_ui_interactions

logger = logging.getLogger(__name__)

