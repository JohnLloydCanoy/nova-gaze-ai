import os
import time
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QBuffer, QIODevice
import pyautogui

from app.aws_nova.client import NovaAIClient

logger = logging.getLogger(__name__)

def capture_screen(
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
        # Hide the application window cleanly
        main_window.hide()
        
        # Force the Qt event loop to process the hide event immediately
        QApplication.processEvents()
        
        # Brief pause to ensure the OS compositor has fully cleared the window visually
        time.sleep(0.2) 
        
        # Capture the screen and save to disk
        logger.info(f"Capturing screenshot to {file_path}")
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        
    except Exception as capture_error:
        logger.error(f"Failed to capture screenshot: {capture_error}")
        # Make sure the window comes back if capturing fails
        main_window.show()
        raise RuntimeError(f"Screenshot capture failed: {capture_error}")

    try:
        # Restore the application window as quickly as possible for good UX
        main_window.show()
        QApplication.processEvents()
        
        # Submit to Nova client
        # (Note: adjust '.analyze_vision' to match your actual client method)
        logger.info("Submitting screenshot and message to Nova AI.")
        response = nova_client.analyze_vision(
            image_path=file_path,
            prompt=chat_message
        )
        
        return response
        
    except Exception as api_error:
        logger.error(f"Failed to communicate with Nova AI: {api_error}")
        raise
        
    finally:
        # Security & Scalability: Clean up the file so we don't leak user data or fill up the disk
        if cleanup_after and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
            except OSError as cleanup_error:
                logger.warning(f"Could not remove temporary screenshot {file_path}: {cleanup_error}")