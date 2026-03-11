# This is a function where we take a screen shot of the user's screen and save it to a file. We will use the pyautogui library to take the screen shot and save it to a file. We will also use the screenshot to be submitted to the Nova client for analysis. This is a crucial part of the app as it allows us to capture the user's screen and provide insights based on the visual data. We will also briefly hide the app window to ensure we capture a clean screenshot of the desktop without our own interface in it. this function will be called when the user submits a chat message, allowing us to provide context-aware responses based on the current state of the user's screen. 
import os
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QBuffer, QIODevice
import pyautogui
from app.aws_nova.client import NovaAIClient


logger = logging.getLogger(__name__)

def process_chat_with_screenshot(
    main_window, 
    nova_client: NovaAIClient, 
    chat_message: str, 
    file_path: str = "temp_screenshot.png",
    cleanup_after: bool = True
    ) -> dict | None:
    """
    Hides the main app window, captures the desktop, saves it to a file, 
    and submits it to Nova AI along with the user's message.
    
    Args:
        main_window: The PyQt6 main window instance to hide/show.
        nova_client: An initialized instance of NovaAIClient.
        chat_message: The context-aware chat message from the user.
        file_path: The destination path for the screenshot.
        cleanup_after: If True, deletes the screenshot after submission for security.
        
    Returns:
        The response from the Nova AI client, or None if it fails.
    """
    
    try:
        main_window.hide()
        QApplication.processEvents()
        